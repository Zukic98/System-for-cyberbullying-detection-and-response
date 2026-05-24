import React, { useState } from 'react';

const InputForm = ({ onAnalyze, loading }) => {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim()) {
      onAnalyze(text.trim());
    }
  };

  const exampleTexts = [
    { emoji: '✅', text: "The weather is beautiful today and I'm feeling great!", label: 'Siguran' },
    { emoji: '🚨', text: "I will find you and kill you, you worthless piece of trash", label: 'Prijetnja' },
    { emoji: '🚫', text: "All immigrants should be deported, they're destroying our culture", label: 'Govor mržnje' },
    { emoji: '⚡', text: "You're being really annoying right now, stop it", label: 'Granični' },
    { emoji: '✅', text: "Great job on the presentation today, really well done!", label: 'Pozitivan' },
  ];

  return (
    <form onSubmit={handleSubmit} className="card p-8">
      <div className="flex items-center gap-3 mb-4">
        <span className="text-3xl">📝</span>
        <label className="text-xl font-bold text-gray-800">
          Unesite tekst za analizu
        </label>
      </div>
      
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Unesite tekst koji želite analizirati na cyberbullying..."
        className="input-field h-36"
        disabled={loading}
      />

      <div className="flex items-center justify-between mt-4">
        <button
          type="submit"
          disabled={loading || !text.trim()}
          className="btn-primary flex items-center gap-2 text-lg"
        >
          {loading ? (
            <>
              <div className="w-5 h-5 rounded-full border-2 border-white border-t-transparent animate-spin"></div>
              Analiziram...
            </>
          ) : (
            <>
              <span>🔍</span> Analiziraj tekst
            </>
          )}
        </button>

        <span className="text-gray-400 text-sm font-medium">
          {text.length} karaktera
        </span>
      </div>

      {/* Primjeri */}
      <div className="mt-6 pt-5 border-t border-gray-100">
        <p className="text-sm font-semibold text-gray-500 mb-3">
          💡 Primjeri za brzo testiranje:
        </p>
        <div className="flex flex-wrap gap-2">
          {exampleTexts.map((example, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setText(example.text)}
              className="tag bg-white border border-gray-200 hover:border-purple-300 hover:bg-purple-50 text-gray-600 hover:text-purple-700 cursor-pointer"
            >
              <span className="mr-1.5">{example.emoji}</span>
              {example.label}
            </button>
          ))}
        </div>
      </div>
    </form>
  );
};

export default InputForm;