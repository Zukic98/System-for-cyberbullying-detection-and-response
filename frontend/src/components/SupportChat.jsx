import React from 'react';

const SupportChat = ({ support, decisionInfo }) => {
  return (
    <div className="space-y-6">
      {/* Poruka podrške */}
      <div className="card p-8">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">💌</span>
          <h3 className="text-xl font-bold text-gray-800">Poruka podrške</h3>
        </div>
        <div className="p-6 rounded-2xl text-gray-700 leading-relaxed text-lg"
             style={{ background: decisionInfo.bgColor, border: `2px solid ${decisionInfo.borderColor}` }}>
          {support.message}
        </div>
      </div>

      {/* Resursi */}
      <div className="card p-8">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">📞</span>
          <h3 className="text-xl font-bold text-gray-800">Resursi za pomoć</h3>
        </div>
        <div className="space-y-3">
          {support.resources.map((res, i) => (
            <div key={i} className="flex items-center gap-4 p-4 bg-purple-50 rounded-2xl hover:bg-purple-100 transition-all cursor-pointer border border-purple-100">
              <span className="text-2xl">{res.name.split(' ')[0]}</span>
              <div>
                <p className="font-semibold text-gray-800">{res.name.substring(2)}</p>
                <p className="text-sm text-purple-600">{res.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sigurnosni savjeti */}
      <div className="card p-8">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">🛡️</span>
          <h3 className="text-xl font-bold text-gray-800">Sigurnosni savjeti</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {support.safety_tips.map((tip, i) => (
            <div key={i} className="flex items-center gap-3 p-4 bg-green-50 rounded-2xl border border-green-100">
              <span className="text-2xl">{tip.split(' ')[0]}</span>
              <span className="text-sm font-medium text-gray-700">{tip.substring(2)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SupportChat;