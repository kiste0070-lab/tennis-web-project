'use client';

import { useState, useEffect } from 'react';

interface LogEntry {
  id: string;
  timestamp: string;
  level: string;
  message: string;
}

export default function Home() {
  const [interval, setIntervalTime] = useState(12);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [showLogs, setShowLogs] = useState(false);
  const [apiUrl, setApiUrl] = useState('');
  const [apiUrlInput, setApiUrlInput] = useState('');

  // 로컬 스토리지에서 API URL 로드
  useEffect(() => {
    const savedUrl = localStorage.getItem('tennis_api_url');
    if (savedUrl) {
      setApiUrl(savedUrl);
      setApiUrlInput(savedUrl);
    }
  }, []);

  // 로그 폴링 (5초마다)
  useEffect(() => {
    if (!showLogs || !apiUrl) return;
    
    const fetchLogs = async () => {
      try {
        const res = await fetch(`${apiUrl}/logs`);
        const data = await res.json();
        setLogs(data.logs || []);
      } catch (e) {
        // 로그 fetching 실패 시 조용히 통과
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, [showLogs, apiUrl]);

  const saveApiUrl = () => {
    const url = apiUrlInput.trim();
    if (!url) return;
    localStorage.setItem('tennis_api_url', url);
    setApiUrl(url);
    setMessage('API URL이 저장되었습니다!');
  };

  const startBot = async () => {
    if (!apiUrl) {
      setMessage('먼저 API URL을 입력하고 저장해 주세요!');
      return;
    }
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch(`${apiUrl}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interval_minutes: interval }),
      });
      const data = await res.json();
      setMessage(data.msg || '봇이 시작되었습니다!');
    } catch (error) {
      setMessage('서버에 연결할 수 없습니다. (서버가 켜져 있는지 확인하세요)');
    }
    setLoading(false);
  };

  const stopBot = async () => {
    if (!apiUrl) {
      setMessage('먼저 API URL을 입력해 주세요!');
      return;
    }
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch(`${apiUrl}/stop`, {
        method: 'POST',
      });
      const data = await res.json();
      setMessage(data.msg || '봇이 중지되었습니다.');
    } catch (error) {
      setMessage('서버에 연결할 수 없습니다.');
    }
    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-slate-900 flex flex-col items-center p-4 text-white font-sans">
      <div className="bg-slate-800 p-8 rounded-2xl shadow-2xl max-w-md w-full border border-slate-700 mb-6">
        <div className="text-center mb-8">
          <span className="text-6xl mb-4 block">🎾</span>
          <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-green-500 tracking-tight">
            테니스 자동 예약
          </h1>
          <p className="text-slate-400 mt-3 text-sm font-medium">Vercel + 로컬 서버</p>
        </div>

        {/* API URL 설정 */}
        <div className="mb-6 p-4 bg-slate-900 rounded-xl border border-slate-600">
          <label className="block text-xs font-medium text-slate-400 mb-2">
            🔗 백엔드 API URL (ngrok 주소)
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={apiUrlInput}
              onChange={(e) => setApiUrlInput(e.target.value)}
              placeholder="https://xxxx.ngrok-free.app"
              className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <button
              onClick={saveApiUrl}
              className="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-2 rounded-lg text-sm font-medium"
            >
              저장
            </button>
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2 pl-1">
              실행 주기 (분)
            </label>
            <input
              type="number"
              value={interval}
              onChange={(e) => setIntervalTime(Number(e.target.value))}
              className="w-full bg-slate-900 border border-slate-600 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all font-semibold text-lg shadow-inner"
              min="1"
            />
          </div>

          <div className="flex gap-4 pt-4">
            <button
              onClick={startBot}
              disabled={loading || !apiUrl}
              className="flex-1 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-400 hover:to-green-500 text-white font-bold py-3 px-4 rounded-xl shadow-[0_0_15px_rgba(16,185,129,0.4)] transform transition-all active:scale-95 disabled:opacity-50"
            >
              ▶ 시작하기
            </button>
            <button
              onClick={stopBot}
              disabled={loading || !apiUrl}
              className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-200 font-bold py-3 px-4 rounded-xl border border-slate-600 transition-all active:scale-95 disabled:opacity-50 shadow-md"
            >
              ⏹ 중지
            </button>
          </div>

          {/* 로그 보기 버튼 */}
          <button
            onClick={() => setShowLogs(!showLogs)}
            className="w-full bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium py-2 px-4 rounded-xl border border-slate-600 transition-all"
          >
            {showLogs ? '🔽 로그 닫기' : '📋 로그 보기'}
          </button>

          {message && (
            <div className={`mt-4 p-4 rounded-xl text-sm font-medium transition-all ${message.includes('수 없습니다') || message.includes('에러') || message.includes('먼저') ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>
              {message}
            </div>
          )}
        </div>

        <div className="mt-10 text-center">
          <p className="text-xs text-slate-500 font-medium tracking-wide">로컬 서버 연동 모드</p>
        </div>
      </div>

      {/* 로그 뷰어 */}
      {showLogs && (
        <div className="bg-slate-800 p-6 rounded-2xl shadow-2xl max-w-2xl w-full border border-slate-700">
          <h2 className="text-xl font-bold text-emerald-400 mb-4">📊 실시간 로그</h2>
          <div className="bg-slate-900 p-4 rounded-xl max-h-96 overflow-y-auto font-mono text-xs">
            {logs.length === 0 ? (
              <p className="text-slate-500">아직 로그가 없습니다...</p>
            ) : (
              logs.slice(-10).map((log) => (
                <div key={log.id} className="mb-1 border-b border-slate-800 pb-1">
                  <span className="text-slate-500">[{log.timestamp}]</span>{' '}
                  <span className={
                    log.level === 'ERROR' ? 'text-red-400' :
                    log.level === 'WARN' ? 'text-yellow-400' :
                    'text-emerald-400'
                  }>[{log.level}]</span>{' '}
                  <span className="text-slate-300">{log.message}</span>
                </div>
              ))
            )}
          </div>
          <p className="text-xs text-slate-500 mt-2 text-center">5초마다 자동 새로고침</p>
        </div>
      )}
    </main>
  );
}