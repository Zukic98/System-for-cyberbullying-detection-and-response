// frontend/src/components/ReportSummary.jsx
import React from 'react';

const ReportSummary = ({ result, summaryResult, sentimentResult, nerResult }) => {
  return (
    <div className="space-y-6">
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
        <h3 className="text-lg font-semibold mb-4">📋 Sažetak incidenta</h3>
        
        <div className="bg-slate-700/50 rounded-lg p-4 text-slate-200">
          {summaryResult.summary}
        </div>
        
        <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
          <div>
            <span className="text-slate-400">Originalna dužina:</span>
            <span className="ml-2 text-white">{summaryResult.original_length} karaktera</span>
          </div>
          <div>
            <span className="text-slate-400">Sažetak:</span>
            <span className="ml-2 text-white">{summaryResult.summary_length} karaktera</span>
          </div>
          <div>
            <span className="text-slate-400">Kompresija:</span>
            <span className="ml-2 text-white">{summaryResult.compression_ratio}%</span>
          </div>
        </div>
      </div>

      {/* Kompletan izvještaj */}
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
        <h3 className="text-lg font-semibold mb-4">📄 Kompletan izvještaj</h3>
        
        <div className="space-y-4 text-sm">
          <ReportRow label="Odluka" value={result.decision} />
          <ReportRow label="Score" value={`${(result.score * 100).toFixed(1)}%`} />
          <ReportRow label="Sentiment" value={sentimentResult?.sentiment || 'N/A'} />
          <ReportRow label="Entiteti" value={nerResult?.total || 0} />
          <ReportRow label="Tip bullying-a" value={result.models.cyberbullying.type} />
          <ReportRow label="Meta napada" value={result.models.target.type} />
          <ReportRow label="Direktna prijetnja" value={result.direct_threat ? 'Da' : 'Ne'} />
        </div>
      </div>
    </div>
  );
};

const ReportRow = ({ label, value }) => (
  <div className="flex justify-between py-2 border-b border-slate-700/50">
    <span className="text-slate-400">{label}</span>
    <span className="text-white font-medium">{typeof value === 'number' ? value : String(value)}</span>
  </div>
);

export default ReportSummary;