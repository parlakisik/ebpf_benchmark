Vagrant.configure("2") do |config|
  config.vm.hostname = "ebpf-benchmark"

  # Detect system architecture and OS
  host_arch = `uname -m`.strip
  host_os = `uname -s`.strip
  is_arm = host_arch == 'arm64'
  is_mac = host_os == 'Darwin'

  # Vagrant box selection based on architecture
  if is_arm && is_mac
    # ARM Mac (Apple Silicon) - use native ARM64 box with QEMU/libvirt
    config.vm.box = "perk/ubuntu-2204-arm64"

    config.vm.provider "qemu" do |qemu|
      qemu.machine = "virt"
      qemu.cpu = "cortex-a72"
      qemu.memory = "4096"
      qemu.smp = "cpus=4,cores=4"
      qemu.qemu_dir = "/usr/local/Cellar/qemu/10.1.2/share/qemu"
      # Use TCG instead of HVF - HVF not supported on macOS for QEMU directly
      qemu.extra_qemu_args = %w(-accel tcg,tb-size=512)
    end
    puts "Using QEMU/libvirt provider with HVF acceleration for ARM64 Mac"
  else
    # Intel Mac or Linux - use VirtualBox
    config.vm.box = "ubuntu/jammy64"
    config.vm.provider "virtualbox" do |vb|
      vb.name = "ebpf-benchmark-vm"
      vb.memory = 4096
      vb.cpus = 4
      vb.customize ["modifyvm", :id, "--cableconnected1", "on"]
    end
    puts "Using VirtualBox provider for #{host_arch} #{host_os}"
  end

  # Shared folder configuration
  # QEMU doesn't support synced folders, so we copy files instead
  config.vm.synced_folder ".", "/vagrant", disabled: true

  # Network configuration
  config.vm.network "private_network", type: "dhcp"

  # Provision the VM
  config.vm.provision "file", source: "provision.sh", destination: "/tmp/provision.sh"
  config.vm.provision "shell", path: "provision.sh", privileged: true

  # Create directories and fix permissions (for QEMU which doesn't support synced folders)
  config.vm.provision "shell", inline: <<-SHELL
    mkdir -p /home/vagrant/ebpf_benchmark
    chown vagrant:vagrant /home/vagrant/ebpf_benchmark
    chmod 755 /home/vagrant/ebpf_benchmark
  SHELL

  # Copy project files to VM
  config.vm.provision "file", source: "src", destination: "/home/vagrant/ebpf_benchmark/src"
  config.vm.provision "file", source: "benchmarks", destination: "/home/vagrant/ebpf_benchmark/benchmarks"
  config.vm.provision "file", source: "Makefile", destination: "/home/vagrant/ebpf_benchmark/Makefile"
  config.vm.provision "file", source: "run_all_benchmarks.py", destination: "/home/vagrant/ebpf_benchmark/run_all_benchmarks.py"
  config.vm.provision "file", source: "generate_benchmark_report.py", destination: "/home/vagrant/ebpf_benchmark/generate_benchmark_report.py"
  config.vm.provision "file", source: "requirements.txt", destination: "/home/vagrant/ebpf_benchmark/requirements.txt"

  # SSH configuration
  config.ssh.forward_x11 = false
end
