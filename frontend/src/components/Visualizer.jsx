import { useEffect, useRef } from "react";

export default function Visualizer({ stream, audioCtx }) {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);

  useEffect(() => {
    if (!stream || !audioCtx) return;

    const source = audioCtx.createMediaStreamSource(stream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 512;
    analyser.smoothingTimeConstant = 0.82;

    // Route to the output at zero gain so the SDK keeps owning playback.
    const gain = audioCtx.createGain();
    gain.gain.value = 0;
    source.connect(analyser);
    analyser.connect(gain);
    gain.connect(audioCtx.destination);

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const timeData = new Uint8Array(analyser.fftSize);
    const freqData = new Uint8Array(analyser.frequencyBinCount);

    const draw = () => {
      rafRef.current = requestAnimationFrame(draw);
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);

      analyser.getByteFrequencyData(freqData);
      analyser.getByteTimeDomainData(timeData);

      // Frequency bars (subtle backdrop).
      const barCount = 48;
      const barWidth = width / barCount;
      ctx.fillStyle = "rgba(37, 99, 235, 0.25)";
      for (let i = 0; i < barCount; i++) {
        const value = freqData[i] / 255;
        const barHeight = Math.max(2, value * height);
        ctx.fillRect(i * barWidth, height - barHeight, barWidth - 2, barHeight);
      }

      // Waveform line.
      ctx.beginPath();
      ctx.strokeStyle = "#4ade80";
      ctx.lineWidth = 2;
      ctx.lineCap = "round";
      const slice = width / timeData.length;
      for (let i = 0; i < timeData.length; i++) {
        const y = (timeData[i] / 128.0) * (height / 2);
        if (i === 0) ctx.moveTo(0, y);
        else ctx.lineTo(i * slice, y);
      }
      ctx.stroke();
    };

    draw();
    return () => {
      cancelAnimationFrame(rafRef.current);
      source.disconnect();
      analyser.disconnect();
      gain.disconnect();
    };
  }, [stream, audioCtx]);

  return <canvas ref={canvasRef} className="visualizer" width={640} height={140} />;
}