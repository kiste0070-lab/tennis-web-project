'use client';

import { useState } from 'react';

export default function Home() {
  const [interval, setIntervalTime] = useState(12);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // 렌더 서버 주소 (추후 Render.com 배포 후 해당 주소로 변경 필요합니다!)
  const API_URL = 'http://localhost:8000'; 

  const startBot = async () => {
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch(`${API_URL}/start`, {
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
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch(`${API_URL}/stop`, {
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
    <main className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-4 text-white font-sans">
      <div className="bg-slate-800 p-8 rounded-2xl shadow-2xl max-w-md w-full border border-slate-700">
        <div className="text-center mb-8">
          <span className="text-6xl mb-4 block">🎾</span>
          <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-green-500 tracking-tight">
            테니스 자동 예약
          </h1>
          <p className="text-slate-400 mt-3 text-sm font-medium">Vercel + Render 봇 컨트롤러</p>
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
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-400 hover:to-green-500 text-white font-bold py-3 px-4 rounded-xl shadow-[0_0_15px_rgba(16,185,129,0.4)] transform transition-all active:scale-95 disabled:opacity-50"
            >
              ▶ 시작하기
            </button>
            <button
              onClick={stopBot}
              disabled={loading}
              className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-200 font-bold py-3 px-4 rounded-xl border border-slate-600 transition-all active:scale-95 disabled:opacity-50 shadow-md"
            >
              ⏹ 중지
            </button>
          </div>

          {message && (
            <div className={`mt-4 p-4 rounded-xl text-sm font-medium transition-all ${message.includes('수 없습니다') || message.includes('에러') ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>
              {message}
            </div>
          )}
        </div>
        
        <div className="mt-10 text-center">
          <p className="text-xs text-slate-500 font-medium tracking-wide">AntiGravity Web Migration Project</p>
        </div>
      </div>
    </main>
  );
}
