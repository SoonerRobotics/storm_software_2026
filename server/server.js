import { createServer } from "http";
import { Server } from "socket.io";

const PORT = 3000;

const httpServer = createServer();
const io = new Server(httpServer, {
  cors: { origin: "*" }
});

let clients = []

io.on("connection", (socket) => {
  clients.push(socket.id);
  console.log('client connected', socket.id);

  if (clients.length === 2) {
    // make the first client the offerer
    io.to(clients[0]).emit("initiateOffer");
  }

  socket.on("offer", sdp => {
    socket.broadcast.emit("getOffer", sdp);
    console.log("sending getOffer, offer: " + socket.id);
  });

  socket.on("answer", sdp => {
    socket.broadcast.emit("getAnswer", sdp);
    console.log("sending getAnswer, answer: " + socket.id);
  });

  socket.on("candidate", candidate => {
    socket.broadcast.emit("getCandidate", candidate);
    console.log("sending candidate, candidate: " + socket.id);
  });
});

httpServer.listen(PORT);

console.log(`listening on port ${PORT}`)