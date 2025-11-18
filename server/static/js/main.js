console.log("Dashboard JS Loaded");

var socket = io();

// Receive High Risk Alerts
socket.on("block_ip", function(data){
    alert("[AUTO BLOCK] IP Blocked: " + data.ip);
});

// Receive Suspicious Alerts
socket.on("suspicious", function(data){
    console.log("Suspicious IP:", data.ip, "Prob:", data.prob);
});
