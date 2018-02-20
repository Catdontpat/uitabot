export class AbstractMessage {
    static get header() {
        return "base";
    }

    str() {
        let obj = Object();
        obj.header = this.constructor.header;
        for(let property in this) {
            obj[property] = String(this[property]);
        }
        return JSON.stringify(obj);
    }
}

export class AuthCodeMessage extends AbstractMessage {
    static get header() {
        return "auth.code";
    }

    constructor(code) {
        super();
        this.code = code;
    }
}

export class AuthFailMessage extends AbstractMessage {
    static get header() {
        return "auth.fail";
    }
}

export class AuthSessionMessage extends AbstractMessage {
    static get header() {
        return "auth.session";
    }

    constructor(handle, secret) {
        super();
        this.handle = handle;
        this.secret = secret;
    }
}

export class AuthSucceedMessage extends AbstractMessage {
    static get header() {
        return "auth.succeed";
    }

    constructor(username, session_handle, session_secret) {
        super();
        this.username = username;
        this.session_handle = session_handle;
        this.session_secret = session_secret;
    }
}

export class PlayURLMessage extends AbstractMessage {
    static get header() {
        return "play.url";
    }

    constructor(url) {
        super();
        this.url = url;
    }
}

const VALID_MESSAGES = {
    "auth.code": [AuthCodeMessage, ["code"]],
    "auth.fail": [AuthFailMessage, []],
    "auth.session": [AuthSessionMessage, ["handle", "secret"]],
    "auth.succeed": [AuthSucceedMessage, ["username", "session_handle", "session_secret"]],
    "play.url": [PlayURLMessage, ["url"]]
};

export class EventDispatcher {
    constructor() {
        this.onAuthFail = m => {}
        this.onAuthSucceed = m => {}
    }

    dispatch(message) {
        if (!message instanceof AbstractMessage) {
            throw new TypeError("EventDispatcher.dispatch requires a subclass of AbstractMessage");
        }
        switch(message.constructor) {
            case AuthFailMessage:
                this.onAuthFail(message);
                break;
            case AuthSucceedMessage:
                this.onAuthSucceed(message);
                break;
            default:
                throw new InternalError("EventDispatcher.dispatch has not implemented this message");
                break;
        }
    }
}

export function parse(message) {
    let obj = JSON.parse(message);
    let args = Array();
    for (let arg of VALID_MESSAGES[obj.header][1]) {
        if (arg in obj) {
            args.push(obj[arg]);
        }
        else {
            throw new TypeError("Mismatched parmeters between parsed message and associated type");
        }
    }
    // This is what modern javascript looks like
    return new (Function.prototype.bind.call(VALID_MESSAGES[obj.header][0], null, ...args));
}
