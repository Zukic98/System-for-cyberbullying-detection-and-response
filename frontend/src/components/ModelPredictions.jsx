import React from 'react';

const ModelPredictions = ({ models }) => {
  if (!models) return null;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
        <span>🤖</span> All 5 Model Predictions
      </h2>
      
      <ModelCard emoji="🔬" title="Model 1: Jigsaw (Toxicity)" color="#8b5cf6">
        <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
          {Object.entries(models.jigsaw).map(([key, val]) => (
            <ModelBadge key={key} label={key.replace(/_/g, ' ')} value={val} />
          ))}
        </div>
      </ModelCard>

      <ModelCard emoji="🏷️" title="Model 2: Cyberbullying Type" color="#06b6d4">
        <div className="flex items-center gap-4 flex-wrap">
          <span className={`px-5 py-2.5 rounded-full text-sm font-bold ${
            models.cyberbullying.is_bullying 
              ? 'bg-red-100 text-red-700 border-2 border-red-200' 
              : 'bg-green-100 text-green-700 border-2 border-green-200'
          }`}>
            {models.cyberbullying.type.replace(/_/g, ' ')}
          </span>
          <span className="text-gray-500 font-medium">
            Confidence: {(models.cyberbullying.confidence * 100).toFixed(1)}%
          </span>
        </div>
      </ModelCard>

      <ModelCard emoji="🚫" title="Model 3: Davidson Hate Speech" color="#ef4444">
        <div className="flex gap-4">
          <ModelBadge label="Hate Speech" value={models.hate_speech.hate} />
          <ModelBadge label="Offensive" value={models.hate_speech.offensive} />
          <ModelBadge label="Neutral" value={models.hate_speech.neutral} />
        </div>
      </ModelCard>

      <ModelCard emoji="🎭" title="Model 4: Formspring (Implicit)" color="#f59e0b">
        <div className="flex gap-4">
          <ModelBadge label="Bullying" value={models.implicit.bullying_prob} />
          <ModelBadge label="Neutral" value={models.implicit.neutral_prob} />
        </div>
      </ModelCard>

      <ModelCard emoji="🎯" title="Model 5: OffensEval (Target)" color="#22c55e">
        <div className="flex items-center gap-4 flex-wrap">
          <span className="px-5 py-2.5 rounded-full text-sm font-bold bg-blue-100 text-blue-700 border-2 border-blue-200">
            {models.target.type}
          </span>
          <span className="text-gray-500 font-medium text-sm">
            Individual: {(models.target.individual_prob * 100).toFixed(0)}% | 
            Group: {(models.target.group_prob * 100).toFixed(0)}%
          </span>
        </div>
      </ModelCard>
    </div>
  );
};

const ModelCard = ({ emoji, title, color, children }) => (
  <div className="card p-6" style={{ borderLeft: `5px solid ${color}` }}>
    <h4 className="font-bold text-gray-800 mb-4 flex items-center gap-2 text-lg">
      <span className="text-2xl">{emoji}</span> {title}
    </h4>
    {children}
  </div>
);

const ModelBadge = ({ label, value }) => {
  const isHigh = value > 0.5;
  return (
    <div className={`px-4 py-3 rounded-xl text-center transition-all hover:scale-105 ${
      isHigh 
        ? 'bg-red-50 border-2 border-red-200' 
        : 'bg-green-50 border-2 border-green-200'
    }`}>
      <p className="text-xs font-semibold text-gray-500 uppercase mb-1">{label}</p>
      <p className={`text-lg font-black ${isHigh ? 'text-red-600' : 'text-green-600'}`}>
        {(value * 100).toFixed(0)}%
      </p>
    </div>
  );
};

export default ModelPredictions;