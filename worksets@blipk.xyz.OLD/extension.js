/*
 * Customised Workspaces extension for Gnome 3
 * This file is part of the Customised Workspaces Gnome Extension for Gnome 3
 * Copyright (C) 2023 A.D. http://github.com/blipk
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * Credits:
 * This extension was created by using the following gnome-shell extensions
 * as a learning resource:
 * - dash-to-panel@jderose9.github.com.v16.shell-extension
 * - clipboard-indicator@tudmotu.com
 * - workspaces-to-dock@passingthru67.gmail.com
 * - workspace-isolated-dash@n-yuki.v14.shell-extension
 * - historymanager-prefix-search@sustmidown.centrum.cz
 * - minimum-workspaces@philbot9.github.com.v9.shell-extension
 * - gsconnect@andyholmes.github.io
 * Many thanks to those great extensions.
 */

// External imports
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
const { extensionUtils, config } = imports.misc;
const { Meta, GLib, Gio, Shell } = imports.gi;
const [major] = config.PACKAGE_VERSION.split('.');
const shellVersion = Number.parseInt(major);

// Internal imports
const _ = imports.gettext.domain(Me.metadata['gettext-domain']).gettext;
import * as sessionManager from './sessionManager.js';

const scopeName = "cw-shell-extension";


function enable() {
    try {


        console.log(scopeName, "@----------|");
        if (Me.session) return; // Already initialized
        global.shellVersion = shellVersion;

        // Maintain compatibility with GNOME-Shell 3.30+ as well as previous versions.
        Me.gScreen = global.screen || global.display;
        Me.gWorkspaceManager = global.screen || global.workspace_manager;
        Me.gMonitorManager = global.screen || (Meta.MonitorManager.get && Meta.MonitorManager.get()) || global.backend.get_monitor_manager();

        // To tune behaviour based on other extensions
        Me.gExtensions = new Object();
        Me.gExtensions.dash2panel = Main.extensionManager.lookup('dash-to-panel@jderose9.github.com');
        Me.gExtensions.dash2dock = Main.extensionManager.lookup('dash-to-dock@micxgx.gmail.com');

        Me.settings = extensionUtils.getSettings('org.gnome.shell.extensions.worksets');

        // Spawn session
        Me.session = new sessionManager.SessionManager();

        console.log(scopeName, "@~..........|");
    } catch (e) {
        console.log(scopeName, e);
        throw e; // Allow gnome-shell to still catch extension exceptions
    }
}

function disable() {
    try {
        console.log(scopeName, "!~~~~~~~~~~|");

        Me.session.saveSession();
        if (Me.worksetsIndicator) Me.worksetsIndicator.destroy();
        delete Me.worksetsIndicator;
        delete Main.panel.statusArea['WorksetsIndicator'];
        if (Me.workspaceIsolater) Me.workspaceIsolater.destroy();
        delete Me.workspaceIsolater;
        if (Me.workspaceManager) Me.workspaceManager.destroy();
        delete Me.workspaceManager;
        if (Me.workspaceViewManager) Me.workspaceViewManager.destroy();
        delete Me.workspaceViewManager;
        if (Me.session) Me.session.destroy();
        delete Me.session;
        if (Me.settings) Me.settings.run_dispose();
        delete Me.settings;

        console.log(scopeName, "!^^^^^^^^^^|" + '\r\n');
    } catch (e) {
        console.log(scopeName, e);
        throw e; // Allow gnome-shell to still catch extension exceptions
    }

}
