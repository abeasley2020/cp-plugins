# cp-PLUGIN_NAME

PLUGIN_DESCRIPTION

## Install

```
/plugin install cp-PLUGIN_NAME@cp-plugins
```

## Usage

```
/cp-PLUGIN_NAME:hello
```

Describe what each skill does, what input it expects, and what it produces.

## Configuration

If this plugin reads team settings, read them from `%USERPROFILE%\.cp-plugins\config.json` under a section named after the plugin (for example `"PLUGIN_NAME": { }`). Never read configuration from inside the repository. Document every key here.

## Limits

Say what the plugin does not do, so nobody relies on it for that.
