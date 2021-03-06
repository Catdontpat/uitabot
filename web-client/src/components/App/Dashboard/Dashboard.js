// --- Dashboard.js ------------------------------------------------------------
// Component for interacting with the backend bot, contains music list, etc

import "./Dashboard.scss";

import React from "react";
import PropTypes from "prop-types";
import FileUploadDropZone from "./FileUpload/FileUpload";
import Header from "./Header/Header";
import TabSelect from "./TabSelect/TabSelect";
import LivePlaylist from "./LivePlaylist/LivePlaylist";
import SearchBox from "./SearchBox/SearchBox";
import VoiceChannelSelect from "./VoiceChannelSelect/VoiceChannelSelect";
import {EventDispatcher} from "utils/Message";

export default class Dashboard extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            activeTab: "playlist"
        };
    }

    render() {
        const playlistClass =
            "Dashboard-Playlist " +
            (this.state.activeTab=="playlist" ? "" : "hidden-xs");
        const voiceChannelClass =
            "Dashboard-VoiceChannel " +
            (this.state.activeTab=="voice" ? "" : "hidden-xs");

        return (
            <div className="Dashboard">
                {/* Files dropped here are uploaded and queued */}
                <FileUploadDropZone
                    eventDispatcher={this.props.eventDispatcher}
                    discordServer={this.props.discordServer}
                >
                    <div className="Dashboard-Inner">
                        <div className={playlistClass}>
                            {/* Searches for and queues audio */}
                            <SearchBox
                                socket={this.props.socket}
                                eventDispatcher={this.props.eventDispatcher}
                            />
                            {/* Shows current music queue, handles song searches, etc */}
                            <LivePlaylist
                                socket={this.props.socket}
                                eventDispatcher={this.props.eventDispatcher}
                            />
                        </div>
                        <div className={voiceChannelClass}>
                            {/* Controls which channel the bot plays music in */}
                            <VoiceChannelSelect
                                socket={this.props.socket}
                                eventDispatcher={this.props.eventDispatcher}
                            />
                        </div>
                        <div className="Dashboard-TabSelect visible-xs">
                            <TabSelect
                                tabs={[
                                    {id: "playlist", display: "Playlist"},
                                    {id: "voice", display: "Voice Channels"}
                                ]}
                                active={this.state.activeTab}
                                onSelect={id => this.setState({activeTab: id})}
                            />
                        </div>
                        <div className="Dashboard-Header">
                            <Header
                                discordUser={this.props.discordUser}
                                discordServer={this.props.discordServer}
                            />
                        </div>
                    </div>
                </FileUploadDropZone>
            </div>
        );
    }
}

Dashboard.propTypes = {
    // Use empty shapes instead of objects to strictly validate any potential future properties
    discordServer: PropTypes.shape({}).isRequired,
    discordUser: PropTypes.shape({}).isRequired,
    eventDispatcher: PropTypes.instanceOf(EventDispatcher).isRequired,
    socket: PropTypes.instanceOf(WebSocket).isRequired
};
