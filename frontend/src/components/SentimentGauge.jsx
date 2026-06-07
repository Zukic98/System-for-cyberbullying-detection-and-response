import React from 'react';

const SentimentGauge = ({ sentimentResult }) => {
  if (!sentimentResult) return null;

  const compound = sentimentResult.compound;

  // Extract top 3 emotions from the all_emotions object sent by the model
  let top3Emotions = [];
  if (sentimentResult.all_emotions) {
    top3Emotions = Object.entries(sentimentResult.all_emotions)
      .sort((a, b) => b[1] - a[1]) // Sort from highest probability to lowest
      .slice(0, 3); // Take only the first three
  }

  // Dictionary for specific emotion emojis to make the UI dynamic
  const emotionEmojis = {
    // Negativne emocije
    anger: "😡", 
    annoyance: "😑", 
    disappointment: "😞", 
    disapproval: "👎",
    disgust: "🤢", 
    fear: "😨", 
    grief: "😢", 
    nervousness: "😰", 
    sadness: "😭", 
    remorse: "😔", 
    embarrassment: "😳", 

    // Pozitivne emocije
    admiration: "👏",
    amusement: "😄", 
    approval: "👍",
    caring: "🥰", 
    desire: "❤️", 
    excitement: "🤩", 
    gratitude: "🙏",
    joy: "🥳", 
    love: "💖", 
    optimism: "🌅", 
    relief: "😮‍💨", 
    pride: "👑", 

    // Neutralne / Kognitivne emocije
    confusion: "😕", 
    curiosity: "🤔",
    surprise: "😲", 
    realization: "💡",
    neutral: "😐" 
  };

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <h3 className="text-lg font-semibold mb-4">😊 Sentiment & GoEmotions Analysis</h3>
      
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
        <p className="text-sm text-slate-400 mb-2">Compound: {compound.toFixed(3)}</p>

        {/* Primary Detected Emotion */}
        {sentimentResult.top_emotion && (
          <div className="mt-2 px-4 py-1.5 bg-slate-700/50 rounded-full border border-slate-600 text-center">
            <span className="text-sm font-medium text-indigo-300">
              Primary Emotion: {emotionEmojis[sentimentResult.top_emotion] || "🎭"} {sentimentResult.top_emotion.toUpperCase()} ({(sentimentResult.confidence * 100).toFixed(0)}%)
            </span>
          </div>
        )}
      </div>

      {/* Basic Sentiment Details */}
      <div className="grid grid-cols-3 gap-3 mt-6">
        <div className="text-center p-3 bg-green-900/20 rounded-lg border border-green-700/30">
          <p className="text-xs text-slate-400">Positive</p>
          <p className="text-xl font-bold text-green-400">{(sentimentResult.positive * 100).toFixed(0)}%</p>
        </div>
        <div className="text-center p-3 bg-slate-700/30 rounded-lg border border-slate-600/30">
          <p className="text-xs text-slate-400">Neutral</p>
          <p className="text-xl font-bold text-slate-300">{(sentimentResult.neutral * 100).toFixed(0)}%</p>
        </div>
        <div className="text-center p-3 bg-red-900/20 rounded-lg border border-red-700/30">
          <p className="text-xs text-slate-400">Negative</p>
          <p className="text-xl font-bold text-red-400">{(sentimentResult.negative * 100).toFixed(0)}%</p>
        </div>
      </div>

      {/* Top 3 Dominant Emotions */}
      {top3Emotions.length > 0 && (
        <div className="mt-6 pt-4 border-t border-slate-700/60">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Top 3 Dominant Emotions:
          </p>
          <div className="space-y-2">
            {top3Emotions.map(([emotion, value]) => (
              <div key={emotion} className="flex items-center justify-between p-2 bg-slate-900/40 rounded-lg border border-slate-800">
                <span className="text-sm text-slate-300 capitalize flex items-center gap-2">
                  <span>{emotionEmojis[emotion] || "✨"}</span>
                  {emotion}
                </span>
                <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-950/40 px-2 py-0.5 rounded border border-indigo-900/40">
                  {(value * 100).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SentimentGauge;