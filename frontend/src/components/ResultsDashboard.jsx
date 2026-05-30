import React, { useState } from 'react';
import axios from 'axios';
import TopicAnalysis from './TopicAnalysis';

const ResultsDashboard = ({ result, sentimentResult, decisionInfo, topicAnalysis }) => {
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [selectedVerdict, setSelectedVerdict] = useState(null);

  const submitAdminFeedback = async (verdict) => {
    setFeedbackLoading(true);
    setSelectedVerdict(verdict);
    
    try {
      await axios.post('http://localhost:8000/api/admin-feedback', {
        original_text: result.original_text,
        model_decision: result.decision,
        model_score: result.score,
        user_verdict: verdict,
        topic_category: topicAnalysis?.topic_category || null,
        model_predictions: result.models
      });
      
      setFeedbackSubmitted(true);
      // Ne sklanjamo dialog automatski - ostaje zahvala
      // setTimeout(() => setFeedbackSubmitted(false), 3000); // OVO UKLONI
    } catch (error) {
      console.error('Feedback error:', error);
      alert('Error sending feedback');
    } finally {
      setFeedbackLoading(false);
    }
  };

  // Only show feedback buttons for ADMIN_REVIEW AND not yet submitted
  const showFeedbackButtons = result.decision === 'ADMIN_REVIEW' && !feedbackSubmitted;

  return (
    <div className="space-y-6">
      {/* Decision Banner */}
      <div 
        className="rounded-2xl p-6 animate-fadeInUp"
        style={{ 
          background: decisionInfo.gradient,
          border: `2px solid ${decisionInfo.borderColor}`
        }}
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <span className="text-5xl animate-bounce">{decisionInfo.emoji}</span>
            <div>
              <h2 className="text-2xl font-bold" style={{ color: decisionInfo.color }}>
                {decisionInfo.label}
              </h2>
              <p className="text-gray-600 mt-1">
                Analysis score: {(result.score * 100).toFixed(1)}%
              </p>
            </div>
          </div>
          {result.direct_threat && (
            <div className="bg-red-100 text-red-700 px-4 py-2 rounded-full font-semibold animate-pulse">
              🚨 DIRECT THREAT DETECTED
            </div>
          )}
        </div>
      </div>

      {/* Score Bar */}
      <div className="card p-5">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>📊 Threat Level</span>
          <span className="font-bold">{(result.score * 100).toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className="h-3 rounded-full transition-all duration-700"
            style={{ 
              width: `${result.score * 100}%`,
              background: `linear-gradient(90deg, ${decisionInfo.color}80, ${decisionInfo.color})`
            }}
          />
        </div>
      </div>

      {/* ADMIN REVIEW – confirmation buttons (only if not submitted) */}
      {showFeedbackButtons && (
        <div className="card p-5 border-2 border-yellow-400 bg-yellow-50">
          <div className="flex items-start gap-3 mb-4">
            <span className="text-3xl">⚠️</span>
            <div>
              <h3 className="font-bold text-yellow-800">System is not certain</h3>
              <p className="text-sm text-yellow-700 mt-1">
                The AI model could not determine with certainty whether this is cyberbullying.
                <br />Your feedback will help improve the system.
              </p>
            </div>
          </div>
          
          <div className="flex gap-3 mt-3">
            <button
              onClick={() => submitAdminFeedback('BULLYING_DETECTED')}
              disabled={feedbackLoading}
              className="flex-1 px-4 py-3 bg-red-500 text-white rounded-xl font-semibold hover:bg-red-600 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {feedbackLoading && selectedVerdict === 'BULLYING_DETECTED' ? (
                <span className="animate-spin">⏳</span>
              ) : (
                <span>🚨</span>
              )}
              This IS Cyberbullying
            </button>
            <button
              onClick={() => submitAdminFeedback('SAFE')}
              disabled={feedbackLoading}
              className="flex-1 px-4 py-3 bg-green-500 text-white rounded-xl font-semibold hover:bg-green-600 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {feedbackLoading && selectedVerdict === 'SAFE' ? (
                <span className="animate-spin">⏳</span>
              ) : (
                <span>✅</span>
              )}
              This is NOT Cyberbullying
            </button>
          </div>
        </div>
      )}

      {/* Thank you message after feedback (shown instead of buttons) */}
      {result.decision === 'ADMIN_REVIEW' && feedbackSubmitted && (
        <div className="card p-5 border-2 border-green-400 bg-green-50">
          <div className="text-center py-3">
            <p className="text-green-700 font-medium">✅ Thank you for your feedback!</p>
            <p className="text-green-600 text-sm mt-1">Your response has been saved to improve the model.</p>
          </div>
        </div>
      )}

      {/* Topic Analysis */}
      {topicAnalysis && topicAnalysis.is_analyzed !== false && (
        <TopicAnalysis topicAnalysis={topicAnalysis} />
      )}

      {/* Sentiment Preview */}
      {sentimentResult && (
        <div className="card p-5">
          <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
            <h3 className="font-semibold text-gray-800">😊 Sentiment Analysis</h3>
            
            {sentimentResult.top_emotion && (
              <span className="text-xs font-bold bg-indigo-50 text-indigo-600 px-2.5 py-1 rounded-full border border-indigo-100 uppercase tracking-wider">
                Detected: {sentimentResult.top_emotion}
              </span>
            )}
          </div>

          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="bg-green-50 rounded-xl p-3">
              <div className="text-green-600 font-bold">{(sentimentResult.positive * 100).toFixed(0)}%</div>
              <div className="text-xs text-gray-500">Positive</div>
            </div>
            <div className="bg-gray-50 rounded-xl p-3">
              <div className="text-gray-600 font-bold">{(sentimentResult.neutral * 100).toFixed(0)}%</div>
              <div className="text-xs text-gray-500">Neutral</div>
            </div>
            <div className="bg-red-50 rounded-xl p-3">
              <div className="text-red-600 font-bold">{(sentimentResult.negative * 100).toFixed(0)}%</div>
              <div className="text-xs text-gray-500">Negative</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsDashboard;