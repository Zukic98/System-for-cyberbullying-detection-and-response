import React from 'react';

const ResultsDashboard = ({ result, sentimentResult, decisionInfo }) => {
  const score = result.score * 100;

  return (
    <div className="space-y-6">
      {/* Severity Meter */}
      <div className="card p-8">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">📊</span>
          <h3 className="text-xl font-bold text-gray-800">Nivo ozbiljnosti</h3>
        </div>
        
        <div className="relative">
          <div className="flex justify-between mb-3 text-sm font-semibold">
            <span className="text-green-600 flex items-center gap-1">
              <span>✅</span> Sigurno
            </span>
            <span className="text-red-500 flex items-center gap-1">
              <span>🚨</span> Opasno
            </span>
          </div>
          
          <div className="severity-bar">
            <div 
              className="severity-bar-fill"
              style={{ 
                width: `${score}%`,
                background: score > 70 
                  ? 'linear-gradient(90deg, #f87171, #ef4444)' 
                  : score > 30 
                    ? 'linear-gradient(90deg, #fbbf24, #f59e0b)' 
                    : 'linear-gradient(90deg, #34d399, #22c55e)'
              }}
            ></div>
          </div>
          
          <div className="text-center mt-6">
            <div className="inline-flex items-center gap-3 px-6 py-3 rounded-2xl" 
                 style={{ background: decisionInfo.bgColor, border: `2px solid ${decisionInfo.borderColor}` }}>
              <span className="text-4xl">{decisionInfo.emoji}</span>
              <div className="text-left">
                <p className="text-3xl font-black" style={{ color: decisionInfo.color }}>
                  {score.toFixed(1)}%
                </p>
                <p className="text-sm font-medium" style={{ color: decisionInfo.color }}>
                  Bullying Score
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <ScoreCard 
          emoji="🎯"
          title="Odluka sistema"
          value={result.decision.replace('_', ' ')}
          color={decisionInfo.color}
          bgColor={decisionInfo.bgColor}
        />
        <ScoreCard 
          emoji="📈"
          title="Ukupni Score"
          value={`${score.toFixed(1)}%`}
          color={decisionInfo.color}
          bgColor={decisionInfo.bgColor}
        />
        <ScoreCard 
          emoji="😊"
          title="Sentiment"
          value={sentimentResult?.sentiment || 'N/A'}
          color={sentimentResult?.compound > 0 ? '#22c55e' : sentimentResult?.compound < 0 ? '#ef4444' : '#f59e0b'}
          bgColor={sentimentResult?.compound > 0 ? '#f0fdf4' : sentimentResult?.compound < 0 ? '#fef2f2' : '#fffbeb'}
        />
      </div>

      {/* Key Indicators */}
      <div className="card p-8">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">🔑</span>
          <h3 className="text-xl font-bold text-gray-800">Ključni indikatori</h3>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(result.models.jigsaw).map(([key, value]) => (
            <IndicatorBadge key={key} label={key.replace(/_/g, ' ')} value={value} />
          ))}
          <IndicatorBadge label="Hate Speech" value={result.models.hate_speech.hate} />
          <IndicatorBadge label="Implicit Bully" value={result.models.implicit.bullying_prob} />
        </div>
      </div>
    </div>
  );
};

const ScoreCard = ({ emoji, title, value, color, bgColor }) => (
  <div className="card p-6" style={{ borderTop: `4px solid ${color}` }}>
    <div className="flex items-center gap-3 mb-3">
      <span className="text-2xl">{emoji}</span>
      <span className="text-sm font-semibold text-gray-500 uppercase tracking-wide">{title}</span>
    </div>
    <div className="text-2xl font-black" style={{ color }}>
      {value}
    </div>
  </div>
);

const IndicatorBadge = ({ label, value }) => {
  const isHigh = value > 0.5;
  return (
    <div className={`px-4 py-3 rounded-xl text-sm font-semibold flex justify-between items-center transition-all hover:scale-105 ${
      isHigh 
        ? 'bg-red-50 border-2 border-red-200 text-red-700' 
        : 'bg-green-50 border-2 border-green-200 text-green-700'
    }`}>
      <span className="capitalize">{label}</span>
      <span className="font-black text-base">{(value * 100).toFixed(0)}%</span>
    </div>
  );
};

export default ResultsDashboard;