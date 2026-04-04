import { io } from "socket.io-client";

const socket = io("127.0.0.1:3000");

const pc_config = {
  iceServers: []
};

const pc = new RTCPeerConnection(pc_config);

// STORM control WebSocket (to C++ relay)
const CONTROL_SERVER_URL = "ws://192.168.1.123:1909";  // adjust IP as needed
const GUI_SENDER_ID = "3";    // GUI process ID
const CONTROLLER_ID = "1";    // Controller Input process ID

let controlSocket = null;

function connectControlSocket() {
  controlSocket = new WebSocket(CONTROL_SERVER_URL);

  controlSocket.onopen = () => {
    console.log("[GUI] Connected to STORM relay");

    // Send an initial message so relay registers sender "3"
    const hello = {
      sender: GUI_SENDER_ID,
      destination: CONTROLLER_ID,
      data: JSON.stringify({ message_id: 11, connection_status: true })
    };
    controlSocket.send(JSON.stringify(hello));
  };

  controlSocket.onmessage = (event) => {
    const envelope = JSON.parse(event.data);    // { sender, destination, data }
    const payload = JSON.parse(envelope.data);  // inner message with message_id

    if (payload.message_id === 10) {
      // Controller state -> log to GUI for now
      appendLog(
        `LS=(${payload.left_stick_x.toFixed(2)}, ${payload.left_stick_y.toFixed(2)})` +
        ` RS=(${payload.right_stick_x.toFixed(2)}, ${payload.right_stick_y.toFixed(2)})`
      );
    } else if (payload.message_id === 11) {
      appendLog(`Controller connection: ${payload.connection_status}`);
    } else {
      appendLog(`Msg ${payload.message_id} from ${envelope.sender}`);
    }
  };

  controlSocket.onerror = (err) => {
    console.error("[GUI] Control WebSocket error:", err);
  };

  controlSocket.onclose = () => {
    console.log("[GUI] Control socket closed; reconnecting…");
    setTimeout(connectControlSocket, 2000);
  };
}

function appendLog(msg) {
  const logDiv = document.querySelector(".logdiv");
  if (!logDiv) {
    console.warn("logdiv not found");
    return;
  }
  const p = document.createElement("p");
  p.textContent = msg;
  logDiv.appendChild(p);
}

// --- WebRTC / Socket.IO video signaling ---

pc.onicecandidate = e => {
  if (e.candidate) {
    console.log("onicecandidate");
    socket.emit("candidate", e.candidate);
  } else {
    console.log("ICE gathering complete");
  }
};

pc.onconnectionstatechange = e => {
  console.log("connection state change");
  console.log(e);
};

pc.ontrack = ev => {
  console.log("add remote stream success");
  setRemoteStream(ev.streams[0]);
};

socket.on("connect", () => {
  console.log("Connected to signaling server");
});

socket.on("initiateOffer", async () => {
  await setLocalStream();
  await createOffer();
});

socket.on("getOffer", async (sdp) => {
  console.log("Creating answer");
  await setLocalStream();
  await createAnswer(sdp);
});

socket.on("getAnswer", async (sdp) => {
  console.log("Setting remote description");
  await pc.setRemoteDescription(sdp);
});

socket.on("getCandidate", (candidate) => {
  console.log("getCandidate received");
  pc.addIceCandidate(new RTCIceCandidate(candidate)).then(() => {
    console.log("candidate add success");
  });
});

const createOffer = async () => {
  console.log("create offer");
  try {
    const sdp = await pc.createOffer({ offerToReceiveAudio: true, offerToReceiveVideo: true });
    await pc.setLocalDescription(sdp);
    socket.emit("offer", sdp);
  } catch (error) {
    console.error(error);
  }
};

const createAnswer = async (sdp) => {
  try {
    await pc.setRemoteDescription(sdp);
    const answer = await pc.createAnswer({ offerToReceiveAudio: true, offerToReceiveVideo: true });
    await pc.setLocalDescription(answer);
    socket.emit("answer", answer);
  } catch (error) {
    console.error(error);
  }
};

const setLocalStream = async () => {
  try {
    console.log("setting local stream");
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    const video = document.getElementById("localCam");
    video.srcObject = stream;

    stream.getTracks().forEach(track => pc.addTrack(track, stream));
  } catch (error) {
    console.error("Error accessing media devices.", error);
  }
};

const setRemoteStream = async (stream) => {
  try {
    console.log("setting remote stream");
    const remoteVideo = document.getElementById("remoteCam");
    remoteVideo.srcObject = stream;
  } catch (error) {
    console.error("Error accessing remote stream.", error);
  }
};

// Init on page load
window.addEventListener("load", () => {
  connectControlSocket();
  setLocalStream();
});


