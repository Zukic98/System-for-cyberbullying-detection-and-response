import React from 'react';

const ReportSummary = ({ result, summaryResult, sentimentResult, nerResult }) => {
  return (
    <div className="space-y-6">
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
        <h3 className="text-lg font-semibold mb-4">📋 Incident Summary</h3>
        
        <div className="bg-slate-700/50 rounded-lg p-4 text-slate-200">
          {summaryResult.summary}
        </div>
        
        <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
          <div>
            <span className="text-slate-400">Original length:</span>
            <span className="ml-2 text-white">{summaryResult.original_length} characters</span>
          </div>
          <div>
            <span className="text-slate-400">Summary:</span>
            <span className="ml-2 text-white">{summaryResult.summary_length} characters</span>
          </div>
          <div>
            <span className="text-slate-400">Compression:</span>
            <span className="ml-2 text-white">{((1 - summaryResult.summary_length / summaryResult.original_length) * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* Complete Report */}
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
        <h3 className="text-lg font-semibold mb-4">📄 Complete Report</h3>
        
        <div className="space-y-4 text-sm">
          <ReportRow label="Decision" value={result.decision} />
          <ReportRow label="Score" value={`${(result.score * 100).toFixed(1)}%`} />
          <ReportRow label="Sentiment" value={sentimentResult?.sentiment || 'N/A'} />
          <ReportRow label="Entities" value={nerResult?.total || 0} />
          <ReportRow label="Bullying Type" value={result.models.cyberbullying.type} />
          <ReportRow label="Target Type" value={result.models.target.type} />
          <ReportRow label="Direct Threat" value={result.direct_threat ? 'Yes' : 'No'} />
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