import { useState, useEffect, useRef, useCallback } from 'react';
import { tasksAPI } from '../services/api.ts';

const STRIDE_LENGTH_M = 0.762;
const TODAY_KEY = () => `steps_${new Date().toISOString().slice(0, 10)}`;
const AWARDED_KEY = () => `steps_awarded_${new Date().toISOString().slice(0, 10)}`;

function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371000;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

interface WalkTask {
  id: string;
  coins_reward: number;
  completed: boolean;
}

export function useStepTracker(walkTask?: WalkTask, stepGoal?: number) {
  const [steps, setSteps] = useState<number>(() => {
    const saved = localStorage.getItem(TODAY_KEY());
    return saved ? parseInt(saved) : 0;
  });
  const [tracking, setTracking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [goalReached, setGoalReached] = useState(() => !!localStorage.getItem(AWARDED_KEY()));

  const lastPos = useRef<{ lat: number; lon: number } | null>(null);
  const watchId = useRef<number | null>(null);
  const accumulatedDist = useRef<number>(0);
  const awardingRef = useRef(false); // prevent double-fire

  // Auto-award coins when goal is reached
  const tryAwardCoins = useCallback(async (currentSteps: number) => {
    if (!walkTask || walkTask.completed) return;
    if (!stepGoal || currentSteps < stepGoal) return;
    if (localStorage.getItem(AWARDED_KEY())) return; // already awarded today
    if (awardingRef.current) return;

    awardingRef.current = true;
    localStorage.setItem(AWARDED_KEY(), '1');
    setGoalReached(true);

    try {
      await tasksAPI.completeTask(walkTask.id);
      // Notify other screens (Dashboard) to refresh
      window.dispatchEvent(new Event('vitals-logged'));
    } catch (e) {
      // If it fails (e.g. already completed on backend), that's fine
      console.warn('Step goal auto-complete:', e);
    } finally {
      awardingRef.current = false;
    }
  }, [walkTask, stepGoal]);

  const onPosition = useCallback((pos: GeolocationPosition) => {
    const { latitude: lat, longitude: lon, accuracy } = pos.coords;
    if (accuracy > 30) return;

    if (lastPos.current) {
      const dist = haversineDistance(lastPos.current.lat, lastPos.current.lon, lat, lon);
      if (dist < 1) return;
      accumulatedDist.current += dist;
      const newSteps = Math.floor(accumulatedDist.current / STRIDE_LENGTH_M);
      if (newSteps > 0) {
        accumulatedDist.current -= newSteps * STRIDE_LENGTH_M;
        setSteps(prev => {
          const updated = prev + newSteps;
          localStorage.setItem(TODAY_KEY(), String(updated));
          tryAwardCoins(updated);
          return updated;
        });
      }
    }
    lastPos.current = { lat, lon };
  }, [tryAwardCoins]);

  const startTracking = useCallback(() => {
    if (!navigator.geolocation) {
      setError('Geolocation not supported on this device.');
      return;
    }
    setError(null);
    setTracking(true);
    watchId.current = navigator.geolocation.watchPosition(onPosition, (err) => {
      setError(err.message);
      setTracking(false);
    }, { enableHighAccuracy: true, maximumAge: 2000, timeout: 10000 });
  }, [onPosition]);

  const stopTracking = useCallback(() => {
    if (watchId.current !== null) {
      navigator.geolocation.clearWatch(watchId.current);
      watchId.current = null;
    }
    lastPos.current = null;
    setTracking(false);
  }, []);

  const resetSteps = useCallback(() => {
    setSteps(0);
    accumulatedDist.current = 0;
    lastPos.current = null;
    localStorage.setItem(TODAY_KEY(), '0');
  }, []);

  useEffect(() => () => {
    if (watchId.current !== null) navigator.geolocation.clearWatch(watchId.current!);
  }, []);

  return { steps, tracking, error, goalReached, startTracking, stopTracking, resetSteps };
}
