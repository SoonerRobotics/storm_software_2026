import { io } from "socket.io-client";

const socket = io("127.0.0.1:3000");

const pc_config = {
  iceServers: []
}

const pc = new RTCPeerConnection(pc_config);

pc.onicecandidate = e => {
  if (e.candidate) {
    console.log('onicecandidate');
    socket.emit('candidate', e.candidate);
  } else {
    console.log("ICE gathering complete");
  }
}

pc.onconnectionstatechange = e => {
  console.log('connection state change');
  console.log(e);
}

pc.ontrack = ev => {
  console.log('add remote stream success');
  setRemoteStream(ev.streams[0]);
}

socket.on("connect", () => {
  console.log("Connected to signaling server");
});

socket.on("initiateOffer", async () => {
  await setLocalStream();
  await createOffer();
})

socket.on("getOffer", async (sdp) => {
  console.log("Creating answer");
  await setLocalStream();
  await createAnswer(sdp);
})

socket.on("getAnswer", async (sdp) => {
  console.log("Setting remote description")
  await pc.setRemoteDescription(sdp);
})

socket.on("getCandidate", (candidate) => {
  console.log('getCandidate received');
  pc.addIceCandidate(new RTCIceCandidate(candidate)).then(() => {
    console.log('candidate add success');
  })
})

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
    console.log('setting remote stream');
    const remoteVideo = document.getElementById("remoteCam");
    remoteVideo.srcObject = stream;
  } catch (error) {
    console.error("Error accessing remote stream.", error);
  }
}

setLocalStream();