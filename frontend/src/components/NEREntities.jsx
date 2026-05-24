// frontend/src/components/NEREntities.jsx
import React from 'react';

const NEREntities = ({ nerResult }) => {
  if (!nerResult) return null;

  const entityColors = {
    PER: '#ef4444',
    LOC: '#3b82f6',
    ORG: '#22c55e',
    MISC: '#f59e0b',
  };

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <h3 className="text-lg font-semibold mb-4">🔍 Prepoznati entiteti (NER)</h3>
      
      {nerResult.total === 0 ? (
        <p className="text-slate-400 text-center py-4">Nema prepoznatih entiteta</p>
      ) : (
        <div className="space-y-4">
          {Object.entries(nerResult.entities).map(([type, entities]) => 
            entities.length > 0 && (
              <div key={type}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-3 h-3 rounded-full" style={{ backgroundColor: entityColors[type] }}></span>
                  <span className="text-sm font-semibold text-slate-300">
                    {type === 'PER' ? '👤 Osobe' : type === 'LOC' ? '📍 Lokacije' : type === 'ORG' ? '🏢 Organizacije' : '📦 Ostalo'}
                  </span>
                  <span className="text-xs text-slate-500">({entities.length})</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {entities.map((ent, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 rounded-full text-sm"
                      style={{ 
                        backgroundColor: entityColors[type] + '20',
                        color: entityColors[type],
                        border: `1px solid ${entityColors[type]}40`
                      }}
                    >
                      {ent.text}
                    </span>
                  ))}
                </div>
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
};

export default NEREntities;