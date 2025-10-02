import { io } from "socket.io-client";

const socket = io("http://localhost:3000");

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
  console.log(e);
}

pc.ontrack = ev => {
  console.log('add remote stream success');
  setRemoteStream(ev.streams[0]);
}

socket.on("connect", () => {
  console.log("Connected to signaling server");
});

socket.on("initiateOffer", () => {
  createOffer();
})

socket.on("getOffer", (sdp) => {
  console.log("Creating answer");
  createAnswer(sdp);
})

socket.on("getAnswer", (sdp) => {
  console.log("Setting remote description")
  pc.setRemoteDescription(sdp);
})

socket.on("getCandidate", (candidate) => {
  console.log('getCandidate received');
  pc.addIceCandidate(new RTCIceCandidate(candidate)).then(() => {
    console.log('candidate add success');
  })
})

const createOffer = async () => {
  console.log("create offer");
  pc
    .createOffer({ offerToReceiveAudio: true, offerToReceiveVideo: true })
    .then(sdp => {
      pc.setLocalDescription(sdp);
      socket.emit("offer", sdp);
    })
    .catch(error => {
      console.log(error);
    });
};

const createAnswer = async (sdp) => {
  pc.setRemoteDescription(sdp).then(() => {
    console.log("answer set remote description success");
    pc
      .createAnswer({
        offerToReceiveVideo: true,
        offerToReceiveAudio: true,
      })
      .then(sdp1 => {
        console.log("create answer");
        pc.setLocalDescription(sdp1);
        socket.emit("answer", sdp1);
      })
      .catch(error => {
        console.log(error);
      });
  });
};

const setLocalStream = async () => {
  try {
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

// Run automatically when included
setLocalStream();