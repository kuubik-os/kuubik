image_name := env("IMAGE_NAME", "kuubik")
fedora_version := env("FEDORA_VERSION", "44")
bib_image := env("BIB_IMAGE", "quay.io/centos-bootc/bootc-image-builder:latest")
vm_gpu := env("VM_GPU", "Y")
wait_seconds := env("TEST_SSH_WAIT_SECONDS", "1800")

[private]
default:
    @just --list

# remove build and test artifacts
clean:
    rm -rf _build* output test-results vm.log

# format shell scripts with shfmt
format:
    find . -iname '*.sh' -type f -exec shfmt --write {} +

# build a container image target (kuubik, kuubik-nvidia, kuubik-lts or kuubik-lts-nvidia)
build target=image_name tag="latest":
    podman build \
        --pull=newer \
        --build-arg FEDORA_VERSION={{ fedora_version }} \
        --label org.opencontainers.image.version=$(date -u +%Y%m%d).0 \
        --target {{ target }} \
        --tag {{ target }}:{{ tag }} \
        .

[private]
_load-root image:
    #!/usr/bin/env bash
    set -euo pipefail
    [[ "${UID}" -eq 0 ]] && exit 0
    id="$(podman image inspect -f '{{{{.Id}}' {{ image }} 2>/dev/null || true)"
    if [[ -z "${id}" ]]; then
        sudo podman pull {{ image }}
    elif [[ "$(sudo podman image inspect -f '{{{{.Id}}' {{ image }} 2>/dev/null || true)" != "${id}" ]]; then
        podman save {{ image }} | sudo podman load
    fi

# convert a container image to output/image/disk.raw, skipped if already built from the same image
build-disk image=("localhost/" + image_name + ":latest"): (_load-root image)
    #!/usr/bin/env bash
    set -euo pipefail
    id="$(sudo podman image inspect -f '{{{{.Id}}' {{ image }})"
    if [[ -f output/image/disk.raw && "$(cat output/.image-id 2>/dev/null)" == "${id}" ]]; then
        echo "output/image/disk.raw is up to date"
        exit 0
    fi
    tmp="$(mktemp -d -p "${PWD}" _build.XXXXXXXXXX)"
    sudo podman run \
        --rm \
        --privileged \
        --pull=newer \
        --net=host \
        --security-opt label=type:unconfined_t \
        -v "${PWD}/disk_config/disk.toml:/config.toml:ro" \
        -v "${tmp}:/output" \
        -v /var/lib/containers/storage:/var/lib/containers/storage \
        {{ bib_image }} \
        --type raw \
        --use-librepo=True \
        --rootfs=btrfs \
        {{ image }}
    sudo rm -rf output
    sudo mv "${tmp}" output
    echo "${id}" | sudo tee output/.image-id >/dev/null
    sudo chown -R "${SUDO_UID:-$(id -u)}:${SUDO_GID:-$(id -g)}" output

# boot a container image in a qemu VM, web console on localhost:8006+, ssh on localhost:2222
run-vm image=("localhost/" + image_name + ":latest"): (build-disk image)
    #!/usr/bin/env bash
    set -euo pipefail
    port=8006
    while ss -tln | grep -q ":${port} "; do
        port=$((port + 1))
    done
    echo "Connect to http://localhost:${port}"
    (sleep 30 && xdg-open "http://localhost:${port}" 2>/dev/null) &
    podman run \
        --rm \
        --privileged \
        --pull=newer \
        --name kuubik-vm \
        --publish "127.0.0.1:${port}:8006" \
        --publish "127.0.0.1:2222:22" \
        --env CPU_CORES=4 \
        --env RAM_SIZE=8G \
        --env DISK_SIZE=64G \
        --env TPM=Y \
        --env GPU={{ vm_gpu }} \
        --device=/dev/kvm \
        --volume "${PWD}/output/image/disk.raw:/boot.raw" \
        docker.io/qemux/qemu

# run the integration tests against a container image booted in a VM
test image:
    #!/usr/bin/env bash
    set -euo pipefail
    just_bin="$(command -v just)"

    cleanup() {
        set +e
        echo "--- vm.log tail ---"
        tail -n 80 vm.log
        sudo podman rm -f kuubik-vm >/dev/null 2>&1
        [[ -n "${vm_pid:-}" ]] && sudo kill "${vm_pid}" 2>/dev/null
    }
    trap cleanup EXIT

    sudo podman build --build-arg IMAGE={{ image }} -f tests/vm.Containerfile -t localhost/kuubik-test:latest .
    sudo podman build -f tests/Containerfile -t kuubik-test-runner .
    sudo "${just_bin}" build-disk localhost/kuubik-test:latest

    sudo env VM_GPU=N "${just_bin}" run-vm localhost/kuubik-test:latest >vm.log 2>&1 &
    vm_pid=$!

    deadline=$((SECONDS + {{ wait_seconds }}))
    until ss -tln | grep -q ':2222 '; do
        if ! sudo kill -0 "${vm_pid}" 2>/dev/null; then
            echo "VM exited before ssh port opened" >&2
            exit 1
        fi
        if ((SECONDS >= deadline)); then
            echo "ssh port did not open within {{ wait_seconds }}s" >&2
            exit 1
        fi
        sleep 10
    done

    mkdir -p test-results
    sudo podman run --rm --network host \
        -e TEST_SSH_WAIT_SECONDS={{ wait_seconds }} \
        -v "${PWD}/tests/ssh:/ssh:ro,Z" \
        -v "${PWD}/test-results:/tmp/test-results:Z" \
        kuubik-test-runner

# build an image locally and run the integration tests against it (flavor: empty, nvidia, lts or lts-nvidia)
test-vm flavor="":
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{ flavor }}" in
    "") target="{{ image_name }}" ;;
    nvidia) target="{{ image_name }}-nvidia" ;;
    lts) target="{{ image_name }}-lts" ;;
    lts-nvidia) target="{{ image_name }}-lts-nvidia" ;;
    *) echo "Usage: just test-vm [nvidia|lts|lts-nvidia]" >&2; exit 1 ;;
    esac
    sudo "$(command -v just)" build "${target}"
    just test "localhost/${target}:latest"
