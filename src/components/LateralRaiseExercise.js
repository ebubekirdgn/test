import React, { useRef, useState, useEffect, useCallback } from 'react';
import Webcam from "react-webcam";
import { Pose } from '@mediapipe/pose';
import * as cam from '@mediapipe/camera_utils';

function LateralRaiseExercise() {

  // Webcam and canvas references
  const webcamRef = useRef(null);
  const canvasRef = useRef(null);

  // State for counting correct and incorrect raises
  const [correctRaiseCount, setCorrectRaiseCount] = useState(0);
  const [incorrectRaiseCount, setIncorrectRaiseCount] = useState(0);
  const [feedback, setFeedback] = useState(""); // State for feedback messages

  // Ref to track the current arm lift status
  const isArmLiftedRef = useRef(false);

  // Threshold values for angle detection
  const thresholds = {
    SHOULDER_RAISE: [85, 95], // Ideal shoulder raise angle range
    SHOULDER_TOO_LOW: 70, // Minimum angle for a correct raise
    SHOULDER_TOO_HIGH: 100, // Maximum angle for a correct raise
  };

  // Pose detection and feedback function
  const onResults = useCallback((results) => {
    if (webcamRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      canvas.width = webcamRef.current.video.videoWidth;
      canvas.height = webcamRef.current.video.videoHeight;

      // Draw the webcam image on the canvas
      ctx.drawImage(webcamRef.current.video, 0, 0, canvas.width, canvas.height);

      if (results.poseLandmarks) {
        const landmarks = results.poseLandmarks;

        // Function to draw a circle at a landmark point
        const drawLandmark = (x, y, color) => {
          ctx.beginPath();
          ctx.arc(x, y, 5, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        };

        // Function to draw text at a landmark point
        const drawText = (x, y, text) => {
          ctx.fillStyle = "white";
          ctx.font = "16px Arial";
          ctx.fillText(text, x, y);
        };

        // Draw landmarks and calculate angles for both arms
        const leftShoulder = { x: landmarks[11].x * canvas.width, y: landmarks[11].y * canvas.height };
        const leftElbow = { x: landmarks[13].x * canvas.width, y: landmarks[13].y * canvas.height };
        const rightShoulder = { x: landmarks[12].x * canvas.width, y: landmarks[12].y * canvas.height };
        const rightElbow = { x: landmarks[14].x * canvas.width, y: landmarks[14].y * canvas.height };

        // Draw landmarks for left and right arms
        drawLandmark(leftShoulder.x, leftShoulder.y, "yellow");
        drawLandmark(leftElbow.x, leftElbow.y, "red");
        drawLandmark(rightShoulder.x, rightShoulder.y, "yellow");
        drawLandmark(rightElbow.x, rightElbow.y, "red");

        // Function to calculate angle between three points
        const calculateAngle = (a, b, c) => {
          const ab = { x: b.x - a.x, y: b.y - a.y };
          const bc = { x: c.x - b.x, y: c.y - b.y };
          const dotProduct = ab.x * bc.x + ab.y * bc.y;
          const magnitudeAB = Math.sqrt(ab.x * ab.x + ab.y * ab.y);
          const magnitudeBC = Math.sqrt(bc.x * bc.x + bc.y * bc.y);
          const angle = Math.acos(dotProduct / (magnitudeAB * magnitudeBC));
          return (angle * 180) / Math.PI; // Convert to degrees
        };

        // Calculate angles for both arms
        const leftShoulderAngle = calculateAngle({ x: leftShoulder.x, y: 1 }, leftShoulder, leftElbow);
        const rightShoulderAngle = calculateAngle({ x: rightShoulder.x, y: 1 }, rightShoulder, rightElbow);

        // Draw the angles as text on the canvas near the elbows
        drawText(leftElbow.x + 10, leftElbow.y, `${Math.round(leftShoulderAngle)}°`);
        drawText(rightElbow.x + 10, rightElbow.y, `${Math.round(rightShoulderAngle)}°`);

        let correctLift = false;

        // Check if both arms are in the correct angle range
        if (
          leftShoulderAngle >= thresholds.SHOULDER_RAISE[0] &&
          leftShoulderAngle <= thresholds.SHOULDER_RAISE[1] &&
          rightShoulderAngle >= thresholds.SHOULDER_RAISE[0] &&
          rightShoulderAngle <= thresholds.SHOULDER_RAISE[1]
        ) {
          correctLift = true;
          setFeedback("Harika! Kollarını doğru şekilde kaldırdın.");
        } else {
          setFeedback("Kollarını doğru pozisyonda tutmaya çalış.");
        }

        // Detect when the arms are lifted and then lowered
        if (correctLift && !isArmLiftedRef.current) {
          // Arms were just lifted
          isArmLiftedRef.current = true;
        } else if (!correctLift && isArmLiftedRef.current) {
          // Arms were lowered, count the lift
          if (
            (leftShoulderAngle < thresholds.SHOULDER_TOO_LOW) ||
            (rightShoulderAngle < thresholds.SHOULDER_TOO_LOW) ||
            (leftShoulderAngle > thresholds.SHOULDER_TOO_HIGH) ||
            (rightShoulderAngle > thresholds.SHOULDER_TOO_HIGH)
          ) {
            setIncorrectRaiseCount(prevCount => prevCount + 1);
          } else {
            setCorrectRaiseCount(prevCount => prevCount + 1);
          }
          isArmLiftedRef.current = false;
        }
      }
    }
  }, []);

  useEffect(() => {
    const pose = new Pose({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`,
    });

    pose.setOptions({
      modelComplexity: 1,
      smoothLandmarks: true,
      enableSegmentation: false,
      smoothSegmentation: false,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });

    let camera;
    if (webcamRef.current && webcamRef.current.video) {
      camera = new cam.Camera(webcamRef.current.video, {
        onFrame: async () => {
          await pose.send({ image: webcamRef.current.video });
        },
        width: 640,
        height: 480,
      });
      camera.start();
    }

    pose.onResults(onResults);

    return () => {
      if (camera) camera.stop();
    };
  }, [onResults]);

  return (
    <div className="lateral-raise-container">
      <Webcam ref={webcamRef} style={{ display: 'none' }} />
      <canvas ref={canvasRef} className="pose-canvas"></canvas>
      <div className="counts">
        <p>Doğru Sayısı: {correctRaiseCount}</p>
        <p>Yanlış Sayısı: {incorrectRaiseCount}</p>
        <p>Geri Bildirim: {feedback}</p>
      </div>
    </div>
  );
}

export default LateralRaiseExercise;
