"use client";

import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { SkillGraph, SkillNode } from "@/types";

interface SkillGraphVizProps {
  graph: SkillGraph;
  masteredSkills: string[];
  selectedSkill: string | null;
  onSelectSkill: (skillId: string) => void;
}

interface D3Node extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  color: string;
  size: number;
  category: string;
  difficulty: number;
  description: string;
}

interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  relationship: string;
  weight: number;
}

export default function SkillGraphViz({ graph, masteredSkills, selectedSkill, onSelectSkill }: SkillGraphVizProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; node: D3Node | null }>({ x: 0, y: 0, node: null });

  useEffect(() => {
    if (!svgRef.current || !graph.nodes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth || 700;
    const height = svgRef.current.clientHeight || 420;

    const nodes: D3Node[] = graph.nodes.map((n) => ({ ...n }));
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));

    const links: D3Link[] = graph.edges
      .filter((e) => nodeMap.has(e.from) && nodeMap.has(e.to))
      .map((e) => ({
        source: e.from,
        target: e.to,
        relationship: e.relationship,
        weight: e.weight,
      }));

    const g = svg.append("g");

    svg.call(
      d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.4, 2.5])
        .on("zoom", (event) => g.attr("transform", event.transform))
    );

    svg.append("defs").append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -4 8 8")
      .attr("refX", 16)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-4L8,0L0,4")
      .attr("fill", "#cbd5e1");

    const simulation = d3.forceSimulation<D3Node>(nodes)
      .force("link", d3.forceLink<D3Node, D3Link>(links).id((d) => d.id).distance(80))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide<D3Node>().radius((d) => d.size + 10));

    const link = g.append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#e2e8f0")
      .attr("stroke-width", (d) => d.weight * 1.5)
      .attr("stroke-opacity", 0.4)
      .attr("marker-end", "url(#arrowhead)");

    const node = g.append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .attr("class", "skill-node")
      .call(
        d3.drag<SVGGElement, D3Node>()
          .on("start", (event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>, d: D3Node) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>, d: D3Node) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>, d: D3Node) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }) as unknown as (selection: d3.Selection<d3.BaseType | SVGGElement, D3Node, SVGGElement, unknown>) => void
      )
      .on("click", (event, d) => {
        event.stopPropagation();
        onSelectSkill(d.id);
      })
      .on("mouseover", (event, d) => {
        const rect = svgRef.current!.getBoundingClientRect();
        setTooltip({ x: event.clientX - rect.left, y: event.clientY - rect.top - 10, node: d });
      })
      .on("mouseout", () => setTooltip({ x: 0, y: 0, node: null }));

    node.append("circle")
      .attr("r", (d) => d.size / 2 + 2)
      .attr("fill", (d) => masteredSkills.includes(d.id) ? d.color : "#f8fafc")
      .attr("stroke", (d) => {
        if (selectedSkill === d.id) return "#0f172a";
        return masteredSkills.includes(d.id) ? d.color : "#cbd5e1";
      })
      .attr("stroke-width", (d) => selectedSkill === d.id ? 3 : masteredSkills.includes(d.id) ? 2 : 1.5)
      .style("filter", (d) => masteredSkills.includes(d.id) ? `drop-shadow(0 0 6px ${d.color}60)` : "none");

    node.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", (d) => d.size / 2 + 14)
      .attr("fill", (d) => masteredSkills.includes(d.id) ? d.color : "#64748b")
      .attr("font-size", "9px")
      .attr("font-weight", (d) => masteredSkills.includes(d.id) ? "600" : "400")
      .text((d) => d.label);

    node.filter((d) => masteredSkills.includes(d.id))
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("fill", "white")
      .attr("font-size", "10px")
      .text("✓");

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as D3Node).x!)
        .attr("y1", (d) => (d.source as D3Node).y!)
        .attr("x2", (d) => (d.target as D3Node).x!)
        .attr("y2", (d) => (d.target as D3Node).y!);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    return () => { simulation.stop(); };
  }, [graph, masteredSkills, selectedSkill, onSelectSkill]);

  return (
    <div className="relative w-full h-full">
      <svg ref={svgRef} className="w-full h-full" />
      {tooltip.node && (
        <div
          className="absolute pointer-events-none rounded-lg px-3 py-2 text-xs shadow-lg z-10"
          style={{
            left: tooltip.x + 10,
            top: tooltip.y - 40,
            background: "white",
            border: `1px solid ${tooltip.node.color}40`,
            maxWidth: 200,
          }}
        >
          <p className="font-semibold" style={{ color: tooltip.node.color }}>{tooltip.node.label}</p>
          <p className="text-slate-500 mt-0.5">{tooltip.node.description}</p>
          <p className="text-slate-400 mt-1">Difficulty: {"★".repeat(tooltip.node.difficulty)}{"☆".repeat(5 - tooltip.node.difficulty)}</p>
        </div>
      )}
    </div>
  );
}
