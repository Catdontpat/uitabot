// --- file-upload.js ----------------------------------------------------------
// Component for drag and drop file uploads via websocket

import React from "react";
import * as Config from "config";
import * as Message from "./message.js";
import * as Session from "./session.js";

export default class FileUploadDropZone extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
        };
    }


    handleFileDrop(event) {
        event.preventDefault();
        let files = Array();
        for (let file of event.dataTransfer.files) {
            // Only upload files that have an audio/* mime type
            if (RegExp("^audio\\/").test(file.type)) {
                files.push(file);
            }
        }
        this.upload(files);
    }

    handleDragOver(event) {
        event.preventDefault();
        event.dataTransfer.dropEffect = "none";
        // Only allow drop payloads with an item that has an audio/* mime type
        for (let item of event.dataTransfer.items) {
            if (RegExp("^audio\\/").test(item.type)) {
                event.dataTransfer.dropEffect = "copy";
                break;
            }
        }
    }

    upload(files) {
        if (files.length == 0) {
            return;
        }
        // Create a new authenticated socket to do the file uploads from asynchronously without
        // jamming up the send buffer queue
        let eventDispatcher = new Message.EventDispatcher();
        let socket = new WebSocket(Config.bot_url);
        try {
            // Load up the stored credentials that absolutely most likely exist
            let session = Session.load();
            if (session === null) {
                throw new Error("No session cookie");
            }
            // Initialize socket callbacks
            socket.onmessage = e => eventDispatcher.dispatch(Message.parse(e.data));
            socket.onerror = e => console.log(e);
            socket.onopen = e => {
                socket.send(new Message.AuthSessionMessage(session.handle, session.secret).str());
            };
            // After authentication, join the selected server and upload the files
            eventDispatcher.setMessageHandler("auth.succeed", m => {
                try {
                    socket.send(new Message.ServerJoinMessage(this.props.discordServer).str());
                    for (let file of files) {
                        socket.send(new Message.FileUploadStartMessage(file.size).str());
                        const chunk_size = 4096;
                        let start = 0;
                        let end = 0;
                        while (end < file.size) {
                            start = end;
                            end = Math.min(end + chunk_size, file.size);
                            socket.send(file.slice(start, end));
                        }
                    }
                } finally {
                    socket.close(1000);
                }
            });
            // There is a very rare chance that the server side credentials have expired and failed to renew
            eventDispatcher.setMessageHandler("auth.fail", m => {
                alert("File upload authentication failed, try refreshing");
                socket.close(1000);
            });
        } catch (error) {
            alert(`Error uploading files: ${error.message}`);
            socket.close(1000);
        }
    }

    render() {
        return (
            <div
                onDrop={e => this.handleFileDrop(e)}
                onDragOver={e => this.handleDragOver(e)}
                onDragEnter={() => console.log("onDragEnter")}
            >
                <p>file drop zone</p>
            </div>
        );
    }
}
