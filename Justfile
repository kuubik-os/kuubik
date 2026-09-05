# taken from https://github.com/ublue-os/image-template/blob/main/Justfile

export image_name := env("IMAGE_NAME", "kuubik")
export default_tag := env("DEFAULT_TAG", "latest")
export bib_image := env("BIB_IMAGE", "quay.io/centos-bootc/bootc-image-builder:latest")
export fedora_version := env("FEDORA_VERSION", "44")
export testing_env := env("TESTING_ENVIRONMENT", "FALSE")
export vm_gpu := env("VM_GPU", "TRUE")

alias build-vm := build-qcow2
alias rebuild-vm := rebuild-qcow2
alias run-vm := run-vm-qcow2

[private]
default:
    @just --list


###
### Utility
###

# Remove build artifacts and output directory
[group('Utility')]
clean:
    #!/usr/bin/bash
    set -eoux pipefail
    touch _build
    find *_build* -exec rm -rf {} \;
    rm -f previous.manifest.json changelog.md output.env
    rm -rf output/

# Run a command with sudo if not already root
[group('Utility')]
[private]
sudoif command *args:
    #!/usr/bin/bash
    function sudoif(){
        if [[ "${UID}" -eq 0 ]]; then
            "$@"
        elif [[ "$(command -v sudo)" ]]; then
            /usr/bin/sudo "$@" || exit 1
        else
            exit 1
        fi
    }
    sudoif {{ command }} {{ args }}

# Format shell scripts with shfmt
[group('Utility')]
format:
    #!/usr/bin/env bash
    set -eoux pipefail
    if ! command -v shfmt &> /dev/null; then
        echo "shfmt could not be found. Please install it."
        exit 1
    fi
    /usr/bin/find . -iname "*.sh" -type f -exec shfmt --write "{}" ';'

###
### Build Container Image
###

[group('Build Container Image')]
build $target_image=image_name $tag=default_tag:
    #!/usr/bin/env bash
    set -euo pipefail

    rm -rf "${TMPDIR:-/var/tmp}"/buildah-cache*

    podman build \
        --pull=newer \
        --no-cache \
        --build-arg FEDORA_VERSION="${fedora_version}" \
        --build-arg TESTING_ENVIRONMENT="${testing_env}" \
        --label "org.opencontainers.image.version=${fedora_version}.$(date -u +%Y%m%d).0" \
        --target "${target_image}" \
        --tag "${target_image}:${tag}" \
        .

###
### Build VM Image
###

# Ensure a locally-built image is available to rootful podman (copies or pulls as needed)
[private]
_rootful_load_image $target_image=image_name $tag=default_tag:
    #!/usr/bin/bash
    set -eoux pipefail

    if [[ -n "${SUDO_USER:-}" || "${UID}" -eq "0" ]]; then
        echo "Already root or running under sudo, no need to load image from user podman."
        exit 0
    fi

    set +e
    resolved_tag=$(podman inspect -t image "${target_image}:${tag}" | jq -r '.[].RepoTags.[0]')
    return_code=$?
    set -e

    USER_IMG_ID=$(podman images --filter reference="${target_image}:${tag}" --format "{{{{.ID}}}}")

    if [[ $return_code -eq 0 ]]; then
        ID=$(just sudoif podman images --filter reference="${target_image}:${tag}" --format "{{{{.ID}}}}")
        if [[ "$ID" != "$USER_IMG_ID" ]]; then
            COPYTMP=$(mktemp -p "${PWD}" -d -t _build_podman_scp.XXXXXXXXXX)
            just sudoif TMPDIR="${COPYTMP}" podman image scp "${UID}@localhost::${target_image}:${tag}" "root@localhost::${target_image}:${tag}"
            rm -rf "${COPYTMP}"
        fi
    else
        just sudoif podman pull "${target_image}:${tag}"
    fi

# Convert a container image to a bootable disk image via bootc-image-builder
[private]
_build-bib $target_image $tag $type $config: (_rootful_load_image target_image tag)
    #!/usr/bin/env bash
    set -euo pipefail

    BUILDTMP=$(mktemp -p "${PWD}" -d -t _build-bib.XXXXXXXXXX)

    sudo podman run \
        --rm \
        -it \
        --privileged \
        --pull=newer \
        --net=host \
        --security-opt label=type:unconfined_t \
        -v "$(pwd)/${config}:/config.toml:ro" \
        -v "${BUILDTMP}:/output" \
        -v /var/lib/containers/storage:/var/lib/containers/storage \
        "${bib_image}" \
        --type "${type}" \
        --use-librepo=True \
        --rootfs=btrfs \
        "${target_image}:${tag}"

    mkdir -p output
    sudo mv -f "${BUILDTMP}"/* output/
    sudo rmdir "${BUILDTMP}"
    sudo chown -R "${USER}:${USER}" output/

# Build container image then convert to bootable disk image
[private]
_rebuild-bib $target_image $tag $type $config: (build target_image tag) && (_build-bib target_image tag type config)

# Build a qcow2 VM image from the current container image
[group('Build VM Image')]
build-qcow2 $target_image=("localhost/" + image_name) $tag=default_tag: && (_build-bib target_image tag "qcow2" "disk_config/disk.toml")

# Rebuild container image then build qcow2 VM image
[group('Build VM Image')]
rebuild-qcow2 $target_image=("localhost/" + image_name) $tag=default_tag: && (_rebuild-bib target_image tag "qcow2" "disk_config/disk.toml")

# Build a raw VM image from the current container image (skips the qcow2 conversion step)
[group('Build VM Image')]
build-raw $target_image=("localhost/" + image_name) $tag=default_tag: && (_build-bib target_image tag "raw" "disk_config/disk.toml")

# Rebuild container image then build raw VM image
[group('Build VM Image')]
rebuild-raw $target_image=("localhost/" + image_name) $tag=default_tag: && (_rebuild-bib target_image tag "raw" "disk_config/disk.toml")

###
### Run VM
###

# Run a VM image using qemu container (builds the image if not present)
[private]
_run-vm $target_image $tag $type $config:
    #!/usr/bin/bash
    set -eoux pipefail

    image_file="output/${type}/disk.${type}"
    if [[ "${type}" == iso ]]; then
        image_file="output/bootiso/install.iso"
    elif [[ "${type}" == raw ]]; then
        # bootc-image-builder names the final pipeline (and thus the output
        # subdirectory) "image" for the raw type, not "raw".
        image_file="output/image/disk.raw"
    fi

    if [[ ! -f "${image_file}" ]]; then
        just "build-${type}" "${target_image}" "${tag}"
    fi

    port=8006
    while grep -q ":${port}" <<< "$(ss -tunalp)"; do
        port=$(( port + 1 ))
    done
    echo "Using Port: ${port}"
    echo "Connect to http://localhost:${port}"

    run_args=(
        --rm --privileged
        --pull=newer
        --publish "127.0.0.1:${port}:8006"
        --publish "127.0.0.1:2222:22"
        --env "CPU_CORES=4"
        --env "RAM_SIZE=8G"
        --env "DISK_SIZE=64G"
        --env "TPM=Y"
    )

    case "${vm_gpu,,}" in
        1|true|yes|y)  run_args+=(--env "GPU=Y") ;;
        0|false|no|n)  ;;
        *)
            echo "Unsupported VM_GPU value: ${vm_gpu}" >&2
            exit 1
            ;;
    esac

    run_args+=(
        --device=/dev/kvm
        --volume "${PWD}/${image_file}:/boot.${type}"
    )

    (sleep 30 && xdg-open "http://localhost:${port}") &
    podman run "${run_args[@]}" docker.io/qemux/qemu

# Run the qcow2 VM (builds if not present)
[group('Run VM')]
run-vm-qcow2 $target_image=("localhost/" + image_name) $tag=default_tag: && (_run-vm target_image tag "qcow2" "disk_config/disk.toml")

# Run the raw VM (builds if not present)
[group('Run VM')]
run-vm-raw $target_image=("localhost/" + image_name) $tag=default_tag: && (_run-vm target_image tag "raw" "disk_config/disk.toml")

###
### Test
###

# Build a test image from local files, boot it in a VM, run the pytest integration suite against it, and clean up afterward
[group('Test')]
test-vm flavor="":
    #!/usr/bin/env bash
    set -eoux pipefail

    case "{{ flavor }}" in
    "")
        image_name="kuubik"
        tag="latest"
        ;;
    nvidia)
        image_name="kuubik-nvidia"
        tag="nvidia"
        ;;
    *)
        echo "Usage: just test-vm [nvidia]" >&2
        exit 1
        ;;
    esac

    # resolve to an absolute path -- `just` itself may live somewhere not on
    # root's PATH (e.g. a linuxbrew/user-local install), and the `sudo env
    # ... just ...` calls below run in a fresh root environment that won't
    # find a bare `just` by name
    just_bin="$(command -v just)"

    wait_budget="${TEST_SSH_WAIT_SECONDS:-1800}"

    cleanup() {
        set +e
        echo "--- vm.log tail ---"
        tail -n 80 vm.log 2>/dev/null

        echo "--- stopping leftover VM/build containers ---"
        sudo podman ps -a --filter ancestor=docker.io/qemux/qemu --format '{{{{.ID}}}}' | xargs -r sudo podman rm -f
        sudo podman ps -a --filter ancestor="${bib_image}" --format '{{{{.ID}}}}' | xargs -r sudo podman rm -f

        if [[ -n "${vm_pid:-}" ]]; then
            sudo kill "${vm_pid}" 2>/dev/null
        fi
        rm -f vm.pid
    }
    trap cleanup EXIT

    # Full wipe of build artifacts + output/ (container build cache is untouched
    # either way -- podman/dnf caching already handles that). Off by default so
    # re-runs can reuse the previous disk image; set FORCE_CLEAN=TRUE to force a
    # from-scratch rebuild (also the escape hatch if output/ ever ends up in a
    # broken state, e.g. root-owned leftovers from a previous interrupted run).
    if [[ "${FORCE_CLEAN:-FALSE}" == "TRUE" ]]; then
        echo "FORCE_CLEAN=TRUE -- wiping output/ and build artifacts..."
        sudo rm -rf output/
        "${just_bin}" clean
    fi

    echo "Building test image (${image_name}:${tag})..."
    sudo env TESTING_ENVIRONMENT=TRUE "${just_bin}" build "${image_name}" "${tag}"

    echo "Building test runner..."
    sudo podman build -f tests/Containerfile -t kuubik-test-runner .

    # bootc-image-builder names the raw type's output subdirectory "image", not "raw"
    image_file="output/image/disk.raw"
    cache_key_file="output/.build-cache-key"
    cache_key="${image_name}:${tag}:$(sudo podman image inspect --format '{{{{.Id}}}}' "localhost/${image_name}:${tag}")"

    # Skip the (slow) container-to-disk-image conversion entirely when the
    # container image hasn't changed since the last disk build -- bootc-image-builder
    # re-deploying the full set of layers into a fresh btrfs image is the actual
    # bottleneck here, not the podman build (which is already layer-cached).
    if [[ -f "${image_file}" && -f "${cache_key_file}" && "$(cat "${cache_key_file}")" == "${cache_key}" ]]; then
        echo "Disk image already up to date with ${image_name}:${tag} -- reusing output/, skipping bootc-image-builder."
    else
        echo "No up-to-date cached disk image for ${image_name}:${tag} -- rebuilding it..."
        sudo rm -rf output/
        sudo "${just_bin}" build-raw "localhost/${image_name}" "${tag}"
        # sudo runs the whole way through here (no non-root user podman to copy
        # from, unlike the CI flow), so chown back to $USER ourselves so the
        # cache key below -- and any re-run of this recipe -- stays writable
        # without sudo.
        sudo chown -R "${USER}:${USER}" output/
        echo "${cache_key}" >"${cache_key_file}"
    fi

    # raw skips the extra qcow2 conversion pass bootc-image-builder would
    # otherwise do at the end -- doesn't touch the slow steps (pulling and
    # deploying the container image layers), but it's free to skip.
    echo "Booting VM..."
    nohup sudo env VM_GPU=FALSE "${just_bin}" run-vm-raw "localhost/${image_name}" "${tag}" >vm.log 2>&1 &
    vm_pid=$!
    echo "${vm_pid}" >vm.pid
    deadline=$((SECONDS + wait_budget))
    last_phase=""

    while ((SECONDS < deadline)); do
        if ! sudo kill -0 "${vm_pid}" 2>/dev/null; then
            echo "VM launcher process (pid ${vm_pid}) exited early -- qemu never came up." >&2
            exit 1
        fi

        if ss -tln | grep -q ':2222 '; then
            echo "Port 2222 is listening after ${SECONDS}s"
            break
        fi

        phase="booting qemu"
        [[ -f "${image_file}" ]] || phase="still building disk image"
        if [[ "${phase}" != "${last_phase}" ]]; then
            echo "[${SECONDS}s] ${phase}..."
            last_phase="${phase}"
        fi

        sleep 30
    done

    if ! ss -tln | grep -q ':2222 '; then
        echo "Port 2222 never opened within ${wait_budget}s -- VM process is alive but qemu/network never came up." >&2
        exit 1
    fi

    mkdir -p test-results
    sudo podman run --rm --network host \
        -e TEST_SSH_WAIT_SECONDS="${wait_budget}" \
        -v "${PWD}/tests/ssh:/ssh:ro,Z" \
        -v "${PWD}/test-results:/tmp/test-results:Z" \
        kuubik-test-runner
