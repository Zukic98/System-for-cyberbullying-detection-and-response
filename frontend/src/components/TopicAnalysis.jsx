import React from 'react';

const TopicAnalysis = ({ topicAnalysis }) => {
  if (!topicAnalysis) {
    return (
      <div className="card p-6 text-center">
        <div className="text-4xl mb-3">🔍</div>
        <h3 className="font-semibold text-gray-700">No Topic Analysis</h3>
        <p className="text-sm text-gray-500 mt-1">
          No specific topic was detected for this text, or it was not recognized as cyberbullying.
        </p>
      </div>
    );
  }

  const getSeverityStyles = (severity) => {
    const styles = {
      5: { bg: 'bg-red-600', border: 'border-red-700', glow: 'shadow-red-500/30', label: '⚠️ Very Severe' },
      4: { bg: 'bg-orange-500', border: 'border-orange-600', glow: 'shadow-orange-500/30', label: '🔴 Severe' },
      3: { bg: 'bg-yellow-500', border: 'border-yellow-600', glow: 'shadow-yellow-500/30', label: '🟡 Moderate' },
      2: { bg: 'bg-teal-500', border: 'border-teal-600', glow: 'shadow-teal-500/30', label: '🟢 Mild' },
      1: { bg: 'bg-gray-500', border: 'border-gray-600', glow: 'shadow-gray-500/30', label: '⚪ Low' },
    };
    return styles[severity] || styles[1];
  };

  const severityStyle = getSeverityStyles(topicAnalysis.severity);

  return (
    <div className="card overflow-hidden animate-fadeInUp">
      {/* Header */}
      <div className={`${severityStyle.bg} text-white p-5`}>
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🎯</span>
            <div>
              <h3 className="font-bold text-lg">Topic Analysis</h3>
              <p className="text-white/80 text-sm">BERTopic classification</p>
            </div>
          </div>
          <div className={`bg-white/20 px-3 py-1.5 rounded-full text-sm font-medium ${severityStyle.bg}`}>
            {severityStyle.label}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-5">
        {/* Category */}
        <div className="mb-4">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Detected Topic</div>
          <div className="text-xl font-bold text-gray-800">{topicAnalysis.topic_category}</div>
        </div>

        {/* Keywords */}
        {topicAnalysis.keywords && topicAnalysis.keywords.length > 0 && (
          <div className="mb-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">🔑 Keywords</div>
            <div className="flex flex-wrap gap-2">
              {topicAnalysis.keywords.map((keyword, idx) => (
                <span 
                  key={idx}
                  className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-sm font-medium"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Confidence */}
        <div className="mb-4">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>📊 Classification Confidence</span>
            <span>{(topicAnalysis.confidence * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`${severityStyle.bg} rounded-full h-2 transition-all duration-500`}
              style={{ width: `${topicAnalysis.confidence * 100}%` }}
            />
          </div>
        </div>

        {/* Suggested Response */}
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-4 mt-3 border border-purple-100">
          <div className="flex items-start gap-3">
            <span className="text-2xl">💬</span>
            <div>
              <div className="text-xs text-purple-600 font-semibold uppercase tracking-wide mb-1">Support Message</div>
              <p className="text-gray-700 text-sm leading-relaxed">{topicAnalysis.suggested_response}</p>
            </div>
          </div>
        </div>

        {/* Confidence range badge */}
        <div className="mt-4 pt-3 border-t border-gray-100 flex justify-between items-center text-xs text-gray-400">
          <span>🔬 Topic Model: BERTopic (all-mpnet-base-v2)</span>
          {topicAnalysis.confidence > 0.8 ? (
            <span className="text-green-600">✓ High Confidence</span>
          ) : topicAnalysis.confidence > 0.5 ? (
            <span className="text-yellow-600">● Medium Confidence</span>
          ) : (
            <span className="text-gray-400">○ Low Confidence</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default TopicAnalysis;