        from __future__ import annotations

        from collections import Counter, defaultdict
        from datetime import datetime, timedelta, timezone
        from itertools import combinations
        from typing import Iterable

        from . import models
        from .llm import enhance_digest

        TAG_KEYWORDS = {
            'soccer': {'soccer', 'practice', 'game', 'team'},
            'school': {'school', 'exam', 'teacher', 'class'},
            'health': {'doctor', 'sleep', 'rest', 'health'},
            'travel': {'trip', 'travel', 'airport', 'vacation'},
            'celebration': {'birthday', 'won', 'promotion', 'celebrate', 'anniversary'},
            'work': {'meeting', 'deadline', 'office', 'presentation', 'project'},
            'together': {'dinner', 'movie', 'walk', 'park', 'cook'},
        }
        MILESTONE_WORDS = {'birthday', 'promotion', 'graduation', 'won', 'anniversary', 'trip'}
        CARE_WORDS = {'stressed', 'tired', 'overwhelmed', 'busy', 'anxious'}


        def _parse_people(raw: str) -> list[str]:
            return [item.strip() for item in raw.split(',') if item.strip()]


        def _extract_tags(text: str) -> set[str]:
            lowered = text.lower()
            tags = {tag for tag, words in TAG_KEYWORDS.items() if any(word in lowered for word in words)}
            if not tags:
                tags.add('general')
            return tags


        def serialize_person(person: models.Person) -> dict:
            return {
                'id': person.id,
                'name': person.name,
                'role': person.role,
                'love_language': person.love_language,
                'focus': person.focus,
            }


        def serialize_update(update: models.Update) -> dict:
            return {
                'id': update.id,
                'person_id': update.person_id,
                'person_name': update.person.name,
                'category': update.category,
                'text': update.text,
                'mood': update.mood,
                'created_at': update.created_at.isoformat(),
                'tags': sorted(_extract_tags(update.text)),
            }


        def serialize_memory(memory: models.Memory) -> dict:
            return {
                'id': memory.id,
                'title': memory.title,
                'detail': memory.detail,
                'people': _parse_people(memory.people),
                'importance': memory.importance,
                'created_at': memory.created_at.isoformat(),
            }


        def maybe_capture_memory(text: str, people: Iterable[str]) -> tuple[str, str] | None:
            lowered = text.lower()
            if any(word in lowered for word in MILESTONE_WORDS):
                title = f"Milestone: {text[:48].rstrip('.')}"
                detail = f"Captured automatically from a family update involving {', '.join(people)}."
                return title, detail
            return None


        def build_graph(people: list[models.Person], updates: list[models.Update], memories: list[models.Memory]) -> dict:
            node_scores = Counter()
            edge_scores = Counter()
            nodes = []
            for person in people:
                node_scores[person.name] += 3
            for memory in memories:
                participants = _parse_people(memory.people)
                for person in participants:
                    node_scores[person] += 2 + memory.importance
                for left, right in combinations(sorted(set(participants)), 2):
                    edge_scores[(left, right)] += 1 + memory.importance
            for update in updates:
                node_scores[update.person.name] += 1
                tags = _extract_tags(update.text)
                for tag in tags:
                    edge_scores[(update.person.name, tag)] += 1
            seen = set()
            for name, score in node_scores.items():
                nodes.append({'id': name, 'kind': 'person', 'score': score})
                seen.add(name)
            for tag in sorted({right for _, right in edge_scores if right not in seen}):
                nodes.append({'id': tag, 'kind': 'theme', 'score': 1})
            edges = [
                {'source': left, 'target': right, 'weight': weight}
                for (left, right), weight in edge_scores.most_common(12)
            ]
            return {'nodes': nodes, 'edges': edges}


        def generate_suggestions(people: list[models.Person], updates: list[models.Update]) -> list[dict]:
            suggestions = []
            now = datetime.now(timezone.utc)
            by_person = defaultdict(list)
            tag_counts = Counter()
            for update in updates:
                by_person[update.person.name].append(update)
                tag_counts.update(_extract_tags(update.text))
            for person in people:
                if not by_person[person.name]:
                    suggestions.append({
                        'title': f'Check in with {person.name}',
                        'rationale': 'They have no recent updates in the shared space.',
                        'kind': 'connection',
                    })
                    continue
                latest = max(by_person[person.name], key=lambda item: item.created_at)
                if latest.created_at.tzinfo is None:
                    latest_time = latest.created_at.replace(tzinfo=timezone.utc)
                else:
                    latest_time = latest.created_at
                if now - latest_time > timedelta(days=5):
                    suggestions.append({
                        'title': f'Check in with {person.name}',
                        'rationale': 'It has been a few days since their last shared update.',
                        'kind': 'connection',
                    })
                if any(word in latest.text.lower() for word in CARE_WORDS):
                    suggestions.append({
                        'title': f'Create breathing room for {person.name}',
                        'rationale': f"Their latest note mentions stress or fatigue: '{latest.text}'.",
                        'kind': 'support',
                    })
            common_tags = [tag for tag, count in tag_counts.items() if count >= 2 and tag not in {'general', 'work'}]
            for tag in common_tags[:2]:
                suggestions.append({
                    'title': f'Turn {tag} into a shared moment',
                    'rationale': f'Multiple recent updates mention {tag}, which is a good cue for a low-friction family activity.',
                    'kind': 'pattern',
                })
            if not suggestions:
                suggestions.append({
                    'title': 'Capture one small win this week',
                    'rationale': 'A single shared update is enough to keep the household context warm.',
                    'kind': 'habit',
                })
            return suggestions[:6]


        def build_digest(people: list[models.Person], updates: list[models.Update], suggestions: list[dict]) -> str:
            recent = sorted(updates, key=lambda item: item.created_at, reverse=True)[:4]
            lines = []
            for item in recent:
                lines.append(f"{item.person.name} shared a {item.mood} update about {item.category}: {item.text}")
            if suggestions:
                lines.append('Best next step: ' + suggestions[0]['title'] + ' — ' + suggestions[0]['rationale'])
            fallback = ' '.join(lines) if lines else 'Start by adding a lightweight family update.'
            prompt = (
                'People in household: ' + ', '.join(person.name for person in people) + '
' +
                'Recent updates: ' + ' | '.join(lines)
            )
            return enhance_digest(prompt, fallback)
