/* Define kbd custom element */

const proto = window.location.protocol == 'https:' ? 'wss' : 'ws';

const webSocket = new WebSocket(`${proto}://${window.location.host}${window.base_url}/ws`);

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
		this.setAttribute('class', `${this.getAttribute('class')} material-icons`);
		this.innerHTML = this.icon;
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
		this.robot_status = {};
		this.forgetful_status = "";
	};
	update_status(data) {
		if (data.robot_state) {
			const st = data.robot_state;
			let battery_by_percentage = 'fa-battery-empty';
			if (st.battery_level > 50) {
				battery_by_percentage = 'fa-battery-half';
			}
			if (st.battery_level > 75) {
				battery_by_percentage = 'fa-battery-three_quarters';
			}
			if (st.battery_level > 90) {
				battery_by_percentage = 'fa-battery-full';
			}

			this.robot_status = {
				'state': st.working_status,
				'fan': st.fan_status.toLowerCase(),
				'battery_status': st.working_status == 'PileCharging' ? 'fa-bolt' : battery_by_percentage,
				'battery_percentage': st.battery_level
			}
		}
		if (data.objects) {
			if (data.objects.detail) {
				this.forgetful_status = data.objects.detail;
			} else if (data.objects.result) {
				this.forgetful_status = data.objects.result.join(' - ');
			}
		}

		document.querySelector('#yolo').innerHTML = this.forgetful_status;
		document.querySelector('#status').innerHTML = this.robot_status.state;
		document.querySelector('#fan').classList = [`fa fa-fan fan-${this.robot_status.fan}`]
		document.querySelector('#battery_status').classList = [`fa ${this.robot_status.battery_status}`]
		document.querySelector('#battery_percentage').innerHTML = this.robot_status.battery_percentage;

	}
}

const ackStatus = new AckStatus();

webSocket.onmessage = (event) => {
	const data = JSON.parse(event.data);
	console.log(data)
	ackStatus.update_status(data)
}

document.addEventListener("DOMContentLoaded", () => {
	const elems = document.querySelectorAll('.fixed-action-btn');
	M.FloatingActionButton.init(elems, {});
	const container = document.getElementById('video');
	const Hls = window.Hls;
	if (Hls.isSupported()) {
		var hls = new Hls();
		hls.loadSource(`${window.base_url}/static/stream.m3u8`);
		hls.attachMedia(container);
		hls.on(Hls.Events.MANIFEST_PARSED, function() { container.play(); });
	} else if (container.canPlayType('application/vnd.apple.mpegurl')) {
		container.src = `${window.base_url}/static/stream.m3u8`;
		container.addEventListener('canplay', function() { container.play(); });
	}
});
