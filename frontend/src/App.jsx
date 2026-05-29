import React, { useState } from 'react';
import axios from 'axios';
import InputForm from './components/InputForm';
import ResultsDashboard from './components/ResultsDashboard';
import ModelPredictions from './components/ModelPredictions';
import SupportChat from './components/SupportChat';
import NEREntities from './components/NEREntities';
import SentimentGauge from './components/SentimentGauge';
import ReportSummary from './components/ReportSummary';

const API_URL = 'http://localhost:8000';

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [supportResult, setSupportResult] = useState(null);
  const [nerResult, setNerResult] = useState(null);
  const [sentimentResult, setSentimentResult] = useState(null);
  const [summaryResult, setSummaryResult] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [topicAnalysis, setTopicAnalysis] = useState(null);

  const handleAnalyze = async (text) => {
    setLoading(true);
    try {
      const [analysisRes, supportRes, nerRes, sentimentRes, summaryRes] = await Promise.all([
        axios.post(`${API_URL}/api/analyze`, { text }),
        axios.post(`${API_URL}/api/support`, { text }),
        axios.post(`${API_URL}/api/ner`, { text }),
        axios.post(`${API_URL}/api/sentiment`, { text }),
        axios.post(`${API_URL}/api/summarize`, { text }),
      ]);

      setResult(analysisRes.data);
      setSupportResult(supportRes.data);
      setNerResult(nerRes.data);
      setSentimentResult(sentimentRes.data);
      setSummaryResult(summaryRes.data);
      if (analysisRes.data.topic_analysis) {
        setTopicAnalysis(analysisRes.data.topic_analysis);
      } else {
        setTopicAnalysis(null);
      }

    } catch (error) {
      console.error('API Error:', error);
      alert('⚠️ Analysis error. Check if backend is running at http://localhost:8000');
    }
    setLoading(false);
  };

  const getDecisionInfo = (decision) => {
    switch (decision) {
      case 'BULLYING_DETECTED':
        return {
          color: '#ef4444',
          bgColor: '#fef2f2',
          borderColor: '#fecaca',
          emoji: '🚨',
          gradient: 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)',
          label: 'Cyberbullying Detected'
        };
      case 'ADMIN_REVIEW':
        return {
          color: '#f59e0b',
          bgColor: '#fffbeb',
          borderColor: '#fde68a',
          emoji: '⚡',
          gradient: 'linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)',
          label: 'Admin Review'
        };
      case 'SAFE':
        return {
          color: '#22c55e',
          bgColor: '#f0fdf4',
          borderColor: '#bbf7d0',
          emoji: '✅',
          gradient: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
          label: 'Safe Text'
        };
      default:
        return {
          color: '#6b7280',
          bgColor: '#f9fafb',
          borderColor: '#e5e7eb',
          emoji: '❓',
          gradient: 'linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)',
          label: 'Unknown'
        };
    }
  };

  const decisionInfo = result ? getDecisionInfo(result.decision) : null;

  const tabs = [
    { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
    { id: 'models', label: '🤖 Models', icon: '🤖' },
    { id: 'support', label: '💌 Support', icon: '💌' },
    { id: 'entities', label: '🔍 Analysis', icon: '🔍' },
    { id: 'report', label: '📋 Report', icon: '📋' },
  ];

  return (
    <div className="min-h-screen dot-pattern">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md shadow-sm sticky top-0 z-50 border-b border-purple-100">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="animate-float">
                <span className="text-4xl">🛡️</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold">
                  <span className="gradient-text">CyberBullying</span>
                  <span className="text-gray-700"> Detector</span>
                </h1>
                <p className="text-sm text-gray-500">AI-powered cyberbullying detection & support system</p>
              </div>
            </div>
            
            {decisionInfo && (
              <div 
                className="flex items-center gap-3 px-5 py-2.5 rounded-full animate-bounce-in"
                style={{ 
                  background: decisionInfo.gradient,
                  border: `2px solid ${decisionInfo.borderColor}`
                }}
              >
                <span className="text-2xl">{decisionInfo.emoji}</span>
                <span className="font-bold" style={{ color: decisionInfo.color }}>
                  {decisionInfo.label}
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Input Form */}
        <div className="animate-fadeInUp">
          <InputForm onAnalyze={handleAnalyze} loading={loading} />
        </div>

        {loading && (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="relative">
              <div className="w-20 h-20 rounded-full border-4 border-purple-200 border-t-purple-600 animate-spin"></div>
              <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-3xl animate-pulse">
                🔍
              </span>
            </div>
            <p className="mt-6 text-gray-600 font-medium text-lg">Analyzing text...</p>
            <p className="text-gray-400 text-sm mt-1">5 AI models processing your input</p>
          </div>
        )}

        {result && !loading && (
          <>
            {/* Tabs */}
            <div className="mt-8 animate-fadeInUp">
              <div className="flex gap-1 bg-white rounded-2xl p-1.5 shadow-sm border border-gray-100 overflow-x-auto">
                {tabs.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-5 py-2.5 rounded-xl font-medium transition-all whitespace-nowrap flex items-center gap-2 ${
                      activeTab === tab.id 
                        ? 'bg-purple-600 text-white shadow-md' 
                        : 'text-gray-600 hover:bg-purple-50 hover:text-purple-600'
                    }`}
                  >
                    <span className="text-lg">{tab.icon}</span>
                    <span className="hidden sm:inline">{tab.label.split(' ')[1]}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Tab Content */}
            <div className="mt-6 animate-fadeInUp">
              {activeTab === 'dashboard' && (
                <ResultsDashboard 
                  result={result} 
                  sentimentResult={sentimentResult}
                  decisionInfo={decisionInfo}
                  topicAnalysis={topicAnalysis}
                />
              )}
              {activeTab === 'models' && (
                <ModelPredictions models={result.models} />
              )}
              {activeTab === 'support' && supportResult && (
                <SupportChat support={supportResult} decisionInfo={decisionInfo} />
              )}
              {activeTab === 'entities' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <NEREntities nerResult={nerResult} />
                  <SentimentGauge sentimentResult={sentimentResult} />
                </div>
              )}
              {activeTab === 'report' && summaryResult && (
                <ReportSummary 
                  result={result}
                  summaryResult={summaryResult}
                  sentimentResult={sentimentResult}
                  nerResult={nerResult}
                  decisionInfo={decisionInfo}
                />
              )}
            </div>
          </>
        )}

        {!result && !loading && (
          <div className="text-center py-16 animate-fadeInUp">
            <div className="animate-float inline-block">
              <span className="text-8xl">🔍</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-700 mt-6">
              Enter text for analysis
            </h2>
            <p className="text-gray-500 mt-2 max-w-md mx-auto">
              Our system will analyze the text through 5 advanced AI models and provide a detailed report
            </p>
            
            {/* Feature cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-10 max-w-3xl mx-auto">
              {[
                { emoji: '🔬', label: 'Toxicity\ndetection' },
                { emoji: '🏷️', label: 'Attack\ntype' },
                { emoji: '🚫', label: 'Hate\nspeech' },
                { emoji: '😊', label: 'Sentiment\nanalysis' },
                { emoji: '💌', label: 'Victim\nsupport' },
              ].map((item, i) => (
                <div key={i} className="card p-4 text-center animate-fadeInUp" style={{ animationDelay: `${i * 0.1}s` }}>
                  <span className="text-3xl block mb-2">{item.emoji}</span>
                  <span className="text-xs text-gray-600 whitespace-pre-line">{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;