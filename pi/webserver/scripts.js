let lastIndex = null;
let reconnectInterval = 1000;
const maxReconnectInterval = 16000;
var socket = null;
createSocket();

const soundChartElement = document.getElementById("soundChart");
const emissionsChartElement = document.getElementById("emissionsChart");
const tempChartElement = document.getElementById("tempChart");
const rpmChartElement = document.getElementById("rpmChart");

const soundChart = new Chart(soundChartElement, {
    type: 'line',
    data: {
        labels: Array.from({ length: 60 }, (_, i) => `T-${i}`).reverse(),
        datasets: [
            {
                label: "Engine",
                data: []
            },
            {
                label: "Operator",
                data: []
            }
        ]
    },
    options: {
        animation: {
            duration: 0
        }
    }
});
const emissionsChart = new Chart(emissionsChartElement, {
    type: 'line',
    data: {
        labels: Array.from({ length: 60 }, (_, i) => `T-${i}`).reverse(),
        datasets: [
            {
                label: "Engine",
                data: []
            },
            {
                label: "Operator",
                data: []
            }
        ]
    },
    options: {
        animation: {
            duration: 0
        }
    }
});
const tempChart = new Chart(tempChartElement, {
    type: 'line',
    data: {
        labels: Array.from({ length: 60 }, (_, i) => `T-${i}`).reverse(),
        datasets: [
            {
                label: "Engine",
                data: []
            },
            {
                label: "Exhaust",
                data: []
            }
        ]
    },
    options: {
        animation: {
            duration: 0
        }
    }
});
const rpmChart = new Chart(rpmChartElement, {
    type: 'line',
    data: {
        labels: Array.from({ length: 60 }, (_, i) => `T-${i}`).reverse(),
        datasets: [{
            label: "Engine",
            data: []
        }]
    },
    options: {
        animation: {
            duration: 0
        }
    }
});

function transpose(matrix) {
    let new_matrix = [];
    for (let i = 0; i < matrix[0].length; i++) {
        new_matrix[i] = [];
        for (let j = 0; j < matrix.length; j++) {
            new_matrix[i][j] = matrix[j][i];
        }
    }
    return new_matrix;
}

function createSocket() {
    socket = new WebSocket("ws://" + window.location.host + "/ws");

    socket.onopen = () => {
        console.log("WebSocket connection established");
        socket.send(JSON.stringify({ type: "request_data" })); // Request initial data
    };

    socket.onmessage = (event) => {
        const res_data = JSON.parse(event.data);
        if (res_data.type === "data_update") {
            if (lastIndex === res_data.last_index) return;
            lastIndex = res_data.last_index;
            const transposedData = transpose(res_data.data);

            soundChart.data.datasets.forEach((dataset, index) => {
                dataset.data = transposedData[index];
            });
            emissionsChart.data.datasets.forEach((dataset, index) => {
                dataset.data = transposedData[2 + index];
            });
            tempChart.data.datasets.forEach((dataset, index) => {
                dataset.data = transposedData[4 + index];
            });
            rpmChart.data.datasets.forEach((dataset, index) => {
                dataset.data = transposedData[6 + index];
            });

            soundChart.update();
            emissionsChart.update();
            tempChart.update();
            rpmChart.update();
        } else if (res_data.type === "record_status") {
            console.log(res_data.message);
        } else if (res_data.type === "record_start") {
            alert("Recording started!");
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else if (res_data.type === "record_stop") {
            alert("Recording finished!");
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    };

    socket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };

    socket.onclose = (event) => {
        console.log('WebSocket closed', event);
        attemptReconnect();
    };
}

function attemptReconnect() {
    if (reconnectInterval <= maxReconnectInterval) {
        console.log(`Reconnecting in ${reconnectInterval / 1000} seconds...`);
        setTimeout(() => {
            createSocket();
            reconnectInterval *= 2; // Exponential backoff
        }, reconnectInterval);
    } else {
        console.log('Max reconnect attempts reached');
    }
}

const startBtn = document.getElementById('recording-start');
const stopBtn = document.getElementById('recording-stop');
const secondsInput = document.getElementById('recoding-seconds');

startBtn.addEventListener('click', () => {
    const seconds = parseInt(secondsInput.value, 10);
    if (seconds >= 1 && seconds <= 600) {
        console.log(`Recording started for ${seconds} seconds`);
        socket.send(JSON.stringify({ type: "record", action: "start", duration: seconds }));
        startBtn.disabled = true;
        stopBtn.disabled = false;
    } else {
        alert('Please enter a value between 1 and 600 seconds.');
    }
});

stopBtn.addEventListener('click', () => {
    console.log("Recording stopped");
    socket.send(JSON.stringify({ type: "record", action: "stop" }));
    stopBtn.disabled = true;
    startBtn.disabled = false;
});
