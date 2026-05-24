// frontend/src/components/SentimentGauge.jsx
import React from 'react';

const SentimentGauge = ({ sentimentResult }) => {
  if (!sentimentResult) return null;

  const compound = sentimentResult.compound;
  const rotation = (compound + 1) * 90; // -1 do 1 → 0 do 180 stepeni

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <h3 className="text-lg font-semibold mb-4">😊 Sentiment analiza</h3>
      
      {/* Gauge */}
      <div className="flex flex-col items-center">
        <div className="relative w-48 h-24 overflow-hidden">
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-48 h-48 
                          rounded-full border-[16px] border-slate-700"
               style={{
                 clipPath: 'polygon(0 50%, 100% 50%, 100% 100%, 0 100%)'
               }}>
          </div>
        </div>
        
        <div className="text-4xl font-bold mt-2" 
             style={{ color: compound > 0.05 ? '#22c55e' : compound < -0.05 ? '#ef4444' : '#f59e0b' }}>
          {compound > 0.05 ? '😊' : compound < -0.05 ? '😢' : '😐'}
        </div>
        <p className="text-lg font-semibold mt-1 text-slate-200">
          {sentimentResult.sentiment.charAt(0).toUpperCase() + sentimentResult.sentiment.slice(1)}
        </p>
        <p className="text-sm text-slate-400">Compound: {compound.toFixed(3)}</p>
      </div>

      {/* Detalji */}
      <div className="grid grid-cols-3 gap-3 mt-6">
        <div className="text-center p-3 bg-green-900/20 rounded-lg border border-green-700/30">
          <p className="text-xs text-slate-400">Pozitivno</p>
          <p className="text-xl font-bold text-green-400">{(sentimentResult.positive * 100).toFixed(0)}%</p>
        </div>
        <div className="text-center p-3 bg-slate-700/30 rounded-lg border border-slate-600/30">
          <p className="text-xs text-slate-400">Neutralno</p>
          <p className="text-xl font-bold text-slate-300">{(sentimentResult.neutral * 100).toFixed(0)}%</p>
        </div>
        <div className="text-center p-3 bg-red-900/20 rounded-lg border border-red-700/30">
          <p className="text-xs text-slate-400">Negativno</p>
          <p className="text-xl font-bold text-red-400">{(sentimentResult.negative * 100).toFixed(0)}%</p>
        </div>
      </div>
    </div>
  );
};

export default SentimentGauge;