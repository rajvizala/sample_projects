import React, { useState } from 'react';
import { Shield, Link, MessageSquare, Mail, Loader2 } from 'lucide-react';
import { api } from '../utils/api';
import ThreatScore from './ThreatScore';

const tabs = [
  { id: 'email', label: 'Email', icon: Mail },
  { id: 'url', label: 'URL', icon: Link },
  { id: 'message', label: 'Message', icon: MessageSquare },
];

export default function AnalysisForm({ onAnalysisComplete }) {
  const [activeTab, setActiveTab] = useState('email');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const [email, setEmail] = useState({ sender: '', subject: '', body: '' });
  const [url, setUrl] = useState({ url: '', context: '' });
  const [message, setMessage] = useState({ content: '', channel: 'sms' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      let res;
      if (activeTab === 'email') res = await api.analyzeEmail(email);
      else if (activeTab === 'url') res = await api.analyzeUrl(url);
      else res = await api.analyzeMessage(message);
      setResult(res);
      if (onAnalysisComplete) onAnalysisComplete(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      <div className="flex border-b border-gray-800">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); setResult(null); setError(null); }}
              className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-gray-800 text-white border-b-2 border-sky-500'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
              }`}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-4">
        {activeTab === 'email' && (
          <>
            <input
              type="text" placeholder="Sender email address"
              value={email.sender}
              onChange={(e) => setEmail({ ...email, sender: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/30"
              required
            />
            <input
              type="text" placeholder="Email subject"
              value={email.subject}
              onChange={(e) => setEmail({ ...email, subject: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/30"
              required
            />
            <textarea
              placeholder="Email body content"
              value={email.body} rows={5}
              onChange={(e) => setEmail({ ...email, body: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/30 resize-none"
              required
            />
          </>
        )}

        {activeTab === 'url' && (
          <>
            <input
              type="text" placeholder="https://suspicious-site.com/login"
              value={url.url}
              onChange={(e) => setUrl({ ...url, url: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/30"
              required
            />
            <textarea
              placeholder="Context where URL was found (optional)"
              value={url.context} rows={3}
              onChange={(e) => setUrl({ ...url, context: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/30 resize-none"
            />
          </>
        )}

        {activeTab === 'message' && (
          <>
            <select
              value={message.channel}
              onChange={(e) => setMessage({ ...message, channel: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500"
            >
              <option value="sms">SMS</option>
              <option value="chat">Chat</option>
              <option value="social">Social Media</option>
            </select>
            <textarea
              placeholder="Paste the suspicious message here..."
              value={message.content} rows={5}
              onChange={(e) => setMessage({ ...message, content: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/30 resize-none"
              required
            />
          </>
        )}

        <button
          type="submit" disabled={loading}
          className="w-full bg-sky-600 hover:bg-sky-500 disabled:bg-gray-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : <Shield size={18} />}
          {loading ? 'Analyzing...' : 'Analyze for Threats'}
        </button>
      </form>

      {error && (
        <div className="mx-6 mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className={`mx-6 mb-6 p-5 rounded-lg border ${
          result.threat_detected
            ? 'bg-red-500/5 border-red-500/30'
            : 'bg-green-500/5 border-green-500/30'
        }`}>
          <div className="flex items-start gap-4">
            <ThreatScore score={result.threat_score} severity={result.severity} size="lg" />
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-lg mb-1">
                {result.threat_detected ? 'Threat Detected' : 'No Significant Threat'}
              </h3>
              <p className="text-sm text-gray-400 mb-3">{result.analysis_summary}</p>
              <div className="space-y-2">
                {result.indicators.map((ind, i) => (
                  <div key={i} className="flex items-center gap-3 text-sm">
                    <div className="w-24 bg-gray-800 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          ind.score > 70 ? 'bg-red-500' : ind.score > 40 ? 'bg-amber-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${ind.score}%` }}
                      />
                    </div>
                    <span className="text-gray-300 w-14 text-right">{ind.score}%</span>
                    <span className="text-gray-400">{ind.name}</span>
                  </div>
                ))}
              </div>
              {result.recommended_action && (
                <div className="mt-3 p-3 bg-gray-800/50 rounded-lg text-sm text-gray-300">
                  <span className="font-medium text-sky-400">Action: </span>
                  {result.recommended_action}
                </div>
              )}
              <p className="text-xs text-gray-600 mt-2">
                Analyzed in {result.processing_time_ms}ms
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
