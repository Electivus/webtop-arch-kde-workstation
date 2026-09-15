package main

import "errors"

func packages(p profile, opts options) (any, error) {
	if opts.restorePackages && opts.registerPackage != "" {
		return nil, errors.New("choose package restoration or source registration")
	}
	if (opts.registerPackage == "") != (opts.packageSource == "") {
		return nil, errors.New("source registration requires --register and --source together")
	}
	c, err := ownedContainer(p)
	if err != nil {
		return nil, err
	}
	if c == nil || !c.State.Running {
		return nil, errors.New("start the workstation before managing extra packages")
	}
	action := []string{"status"}
	if opts.restorePackages {
		action = []string{"restore"}
	} else if opts.registerPackage != "" {
		action = []string{"register", "--package", opts.registerPackage, "--source", opts.packageSource}
	}
	var result map[string]any
	err = dockerJSON(p, &result, append([]string{"exec", "--user", "root", p.Name, "workstation-packages"}, action...)...)
	return result, err
}
