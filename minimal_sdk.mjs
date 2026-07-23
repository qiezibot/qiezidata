// Simulated openclaw/plugin-sdk for qqbot plugin
// Provides the minimal API needed by qqbot plugin v1.6.1

export function emptyPluginConfigSchema() {
  return {};
}

export class ChannelPlugin {
  constructor(config) {
    this.config = config || {};
  }
  get id() { return this.config?.id || "unknown"; }
}

export function delegateCompactionToRuntime() {}
export function onDiagnosticEvent() {}

export const applyAccountNameToChannelSection = () => {};
export const deleteAccountFromConfigSection = () => {};
export const setAccountEnabledInConfigSection = () => {};
