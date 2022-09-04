/* Define kbd custom element */

const webSocket = new WebSocket(`ws://${window.location.host}${window.base_url}/ws`);

class KBDItem extends HTMLElement {

	get action() {
		return this.getAttribute('action').replace('-', '_');
	}

	get icon() {
		if (this.getAttribute('icon')) { return this.getAttribute('icon'); }
		return this.key.split(/(?=[A-Z])/).join('-').toLowerCase()
	}

	get key() {
		return this.getAttribute('key');
	}

	activate() {
		console.log(`Moving ${this.action}`);
		webSocket.send(JSON.stringify({ 'action': this.action }));
	}

	connectedCallback() {
		this.setAttribute('class', `${this.getAttribute('class')} fa fa-${this.icon}`);
		document.addEventListener('keyup', (ev) => {
			if (ev.key == this.key) { this.activate(); }
		});
		this.addEventListener('click', () => {
			this.activate();
		});
	}
}
customElements.define('kbd-ctlr', KBDItem);

class AckStatus {
	constructor() {
		this.robot_status = "unknown";
		this.forgetful_status = "";
	};
	update_status(data) {
		if (data.robot_state) {
			this.robot_status = `${data.robot_state.state} (${data.robot_state.mode})`;
		}
		if (data.objects) {
			if (data.objects.detail) {
				this.forgetful_status = data.objects.detail;
			} else if (data.objects.result) {
				this.forgetful_status = data.objects.result.join(' - ');
			}
		}
		document.querySelector('#state').innerHTML = `${this.robot_status} - ${this.forgetful_status}`;

	}
}

const ackStatus = new AckStatus();

webSocket.onmessage = (event) => {
	const data = JSON.parse(event.data);
	console.log(data)
	ackStatus.update_status(data)
}

document.addEventListener("DOMContentLoaded", () => {
	const container = document.getElementById('video');
	const Hls = window.Hls;
	if (Hls.isSupported()) {
		var hls = new Hls();
		hls.loadSource('/static/stream.m3u8');
		hls.attachMedia(container);
		hls.on(Hls.Events.MANIFEST_PARSED, function() { container.play(); });
	} else if (container.canPlayType('application/vnd.apple.mpegurl')) {
		container.src = '/static/stream.m3u8';
		container.addEventListener('canplay', function() { container.play(); });
	}
});
