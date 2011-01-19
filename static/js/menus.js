var timeout    = 500;
var closetimer = 0;
var item       = 0;

function top_open(_parent, _klass) {
    top_canceltimer();
    top_close();
    item = _parent.find(_klass).css('visibility', 'visible');
}

function top_close() {
    if (item)
        item.css('visibility', 'hidden');
}

function top_timer() {
    closetimer = window.setTimeout(top_close, timeout);
}

function top_canceltimer() {
    if(closetimer) {
        window.clearTimeout(closetimer);
        closetimer = null;
    }
}

