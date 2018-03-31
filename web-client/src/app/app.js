// --- app.js ------------------------------------------------------------------
// Main component containing the frontend app

import React from "react";
import * as Config from "config";
import * as Message from "./message.js";
import * as Session from "./session.js";
import * as DiscordOauth from "./discord-oauth.js";
import Authenticate from "./authenticate.js";
import Dashboard from "./dashboard.js";
import ServerSelect from "./server-select.js";

export default class App extends React.Component {
    constructor(props) {
        super(props);

        // Stores main app state determining auth status, connection, etc
        this.state = {
            authenticated: false,
            connection: WebSocket.CLOSED,
            needLogin: false,
            discordServer: null
        };

        // Interval callback handler for sending heartbeat packets to server
        this.heartbeatInterval = null;
    }

    componentDidMount() {
        // Initialize server event callbacks that need to be handled at the root level
        this.eventDispatcher = new Message.EventDispatcher();

        // Handler for authentication failure
        this.eventDispatcher.setMessageHandler("auth.fail", m => {
            this.setState({needLogin: true})
        });

        // Handler for authentication success
        this.eventDispatcher.setMessageHandler("auth.succeed", m => {
            Session.store({handle: m.session_handle, secret: m.session_secret});
            this.setState({authenticated: true});
            // Server will close connection if it doesn't receive a packet after 90 seconds
            this.heartbeatInterval = setInterval(
                () => this.socket.send(new Message.HeartbeatMessage().str()),
                60000
            );
        });

        // Handler for server kick messages
        this.eventDispatcher.setMessageHandler("server.kick", m => {
            this.setState({discordServer: null})
        });

        // Setup the websocket after we're ready to receive and act on messages
        try {
            console.log(`Connecting to ${Config.bot_url}`);
            this.socket = new WebSocket(Config.bot_url);
            this.socket.onmessage = e => this.eventDispatcher.dispatch(Message.parse(e.data));
            this.socket.onerror = e => console.log(e);
            this.socket.onclose = e => this.onSocketClose();
            this.socket.onopen = e => this.onSocketOpen();
            this.setState({connection: this.socket.readyState});
        }
        catch (e) {
            console.log(e);
            this.setState({connection: WebSocket.CLOSED});
        }
    }

    onSocketOpen() {
        this.setState({connection: WebSocket.OPEN});
    }

    onSocketClose() {
        this.setState({connection: WebSocket.CLOSED});
        clearInterval(this.heartbeatInterval);
    }

    componentWillUnmount() {
        this.socket.close();
        this.eventDispatcher.clearMessageHandler("auth.fail");
        this.eventDispatcher.clearMessageHandler("auth.succeed");
        this.eventDispatcher.clearMessageHandler("server.kick");
    }

    // Big, messy state machine acting as a view router
    render() {
        // Display the login page if authentication has failed
        if (this.state.needLogin) {
            const oauthUrl = DiscordOauth.createOauthUrl(Config.client_id, Config.client_url);
            return <p>need to <a href={oauthUrl}>login</a></p>;
        }

        // Establishing connection with backend, SSL handshake, etc
        if (this.state.connection == WebSocket.CONNECTING) {
            return <p>connecting</p>;
        }

        // Connection error displays when server closes connection
        if (this.state.connection != WebSocket.OPEN) {
            return <p>connection error</p>;
        }

        // Attempt authentication with stored credentials (if they exist)
        if (!this.state.authenticated) {
            return <Authenticate
                socket={this.socket}
                onAuthFail={() => this.setState({needLogin: true})}
            />;
        }

        // Authentication succeeded but we haven't selected a server to play music in yet
        if (this.state.discordServer === null) {
            return <ServerSelect
                socket={this.socket}
                eventDispatcher={this.eventDispatcher}
                onServerSelect={id => this.setState({discordServer: id})}
            />;
        }

        // Main view for queueing music and everything else
        return <Dashboard
            socket={this.socket}
            eventDispatcher={this.eventDispatcher}
            discordServer={this.state.discordServer}
        />;
    }
}
