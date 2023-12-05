//
// Update bug interwiki links presentation
// based on bug status.
//

function get_json(url, links, funct) {
	var object = {};
	var http_request = new XMLHttpRequest();
	http_request.open('GET', url, true);
	http_request.setRequestHeader('Accept', 'application/json');
	http_request.onreadystatechange = function () {
		var done = 4, ok = 200;
		if (http_request.readyState == done && http_request.status == ok) {
			object = JSON.parse(http_request.responseText);
			funct(links, object);
		}
	};
	http_request.send(null);
}

function update_debian_links(links, statuses){
	var bug;

	for (bug in statuses) {
		for (var i in links[bug]) {
			var link = links[bug][i];
			var status = statuses[bug];

			if (status.pending == 'done') {
				var fixed_versions = status.fixed_versions.length ? ' in ' + status.fixed_versions.join(', ') : '';
				link.className = 'interwiki closed-bug';
				link.title = 'Closed' + fixed_versions + ': #' + status.id + ': ' + status.subject;
			} else {
				var found_versions = status.found_versions.length ? ' in ' + status.found_versions.join(', ') : '';
				link.className = 'interwiki open-bug';
				link.title = 'Open' + found_versions + ': #' + status.id + ': ' + status.subject;
			}
		}
	}
}

function update_launchpad_links(links, status){
	for (var i in links) {
		var link = links[i];

		if (status['cgi-status'] != 'ok' ) {
			return;
		}
		if( status['complete'] ){
			link.className = 'interwiki closed-bug';
			link.title = 'Closed: #' + status.id + ': ' + status.title;
		} else {
			link.className = 'interwiki open-bug';
			link.title = 'Open: #' + status.id + ': ' + status.title;
		}
		link.href = status.url;
	}
}

function update_debian(url, links){
	var bug;
	var query = [];
	for (bug in links) {
		query.push('bug=' + bug);
	}

	var querystr = query.join(';');

	// Get bug statuses from script
	get_json(url + '/cgi-bin/bugstatus?' + querystr, links, update_debian_links);
}

function update_launchpad(url, links){
	var bug;
	var query = [];
	for (bug in links) {
		get_json(url + '/cgi-bin/launchpad?bug=' + bug, links[bug], update_launchpad_links);
	}
}

function update_links() {

	// Preparation
	var re = new RegExp('^(\\w+://[^/]+)/.*');
	var loc = re.exec(window.location.href);
	var types = ['debian','launchpad'];
	var interwiki = {
		'DebianBug': 'debian',
		'UbuntuBug':'launchpad',
		'LaunchpadBug':'launchpad'
	};
	var links = undefined;

	// Iterate through the links on the page
	for (var i=0; i < document.links.length; i++) {
		var link = document.links[i];
		var bug = '';
		var type = '';

		if( link.title in interwiki ){
			type = interwiki[link.title];
			bug = link.text;
			if (isNaN(parseInt(bug))) {
				bug = bug.replace(/^[^0-9]/g, '');
				bug = bug.replace(/^[^0-9].*/g, '');
			}
		}

		if( isNaN(parseInt(bug)) ){
			if( link.href.indexOf('://bugs.debian.org/') != -1 ){
				type = 'debian';
				bug = link.href;
				bug = bug.replace(/^https?:\/\/bugs\.debian\.org\/([0-9]+)$/i, '$1');
				bug = bug.replace(/^https?:\/\/bugs\.debian\.org\/mbox:([0-9]+)$/i, '$1');
				bug = bug.replace(/^https?:\/\/bugs\.debian\.org\/cgi-bin\/bugreport\.cgi\?.*bug=([0-9]+).*$/i, '$1');
			} else if( link.href.indexOf('launchpad.net/') != -1 ){
				type = 'launchpad';
				bug = link.href;
				bug = bug.replace(/^http[s]?:\/\/(bugs\.)?launchpad\.net\/.*\/([0-9]+)$/i, '$2');
			}
		}

		if (isNaN(parseInt(bug))) {
			continue;
		}

		bug = parseInt(bug).toString();

		if( links == undefined ){
			links = {};
		}

		if( !(type in links) ){
			links[type] = {};
		}

		if ( !(bug in links[type]) ){
			links[type][bug] = [];
		}

		links[type][bug].push(link);
	}

	if( links == undefined ){
		return;
	}

	if( 'debian' in links ){
		update_debian(loc[1], links['debian']);
	}

	if( 'launchpad' in links ){
		update_launchpad(loc[1], links['launchpad']);
	}
}

function add_load_event( funct ) {
	var old_onload = window.onload;
	if (typeof window.onload != 'function') {
		window.onload = funct;
	} else {
		window.onload = function() {
			old_onload();
			funct();
		}
	}
}

add_load_event( update_links );
