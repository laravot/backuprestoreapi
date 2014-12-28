import ovirtsdk.api
import ovirtsdk.xml
from ovirtsdk.xml import params
import logging

VM_NAME = "VM_FOR_BACKUP"
SNAPSHOT_DESCRIPTION = "SNAPSHOT_DESCRIPTION1"
VM_THAT_PERFORM_BACKUP = "VM_PERFORM_BACKUP"
SERVER = YYYYYYYYYYYY
USERNAME = YYYYYYYYYYYY
PASSWORD = YYYYYYYYYYYY

api = ovirtsdk.api.API(
    url=SERVER,
    username=USERNAME,
    password=PASSWORD,
    insecure=True,
    debug=False
)
logging.basicConfig()
log = logging.getLogger()


###########################BACKUP#################################
vm = api.vms.get(VM_NAME)

#Create a VM snapshot:
vm.snapshots.add(params.Snapshot(description=SNAPSHOT_DESCRIPTION, vm=vm))
while api.vms.get(VM_NAME).status.state == 'image_locked':
    sleep(1)

# Get the snapshot, you can backup the configuration data to be able to
# restore the vm with the same configuration later on
snap = api.vms.get(name=vm.name).snapshots.list(all_content=True, description=SNAPSHOT_DESCRIPTION)[0]
configuration_data = snap.get_initialization().get_configuration().get_data()
print configuration_data

# Find the disk snapshot that you want to backup:
disks = snap.disks.list()
disk = None
for current in disks:
    if current.get_name() == "VM_FOR_BACKUP_Disk1":
        disk = current


# Attach a disk that you want to backup to VM that will backup it
vm_backup = api.vms.get(VM_THAT_PERFORM_BACKUP)
vm_backup.disks.add(disk)


# You can get the device logical name within the VM if needed
# (you should have the ovirt-guest-agent installed within the guest os).
# note it take few minutes for the logical name to be reported from the guest.
diskwithinfo = api.vms.get(VM_THAT_PERFORM_BACKUP).disks.get(id=disk.id)
print diskwithinfo.get_logical_name()

# Detach the backed up disk
detach = params.Action(detach=True)
diskwithinfo.delete(action=detach)


########################### RESTORE #################################
#Create a new VM using the backed up configuration
newVm = params.VM(name="newVm", cluster=api.clusters.get(name='Default'))
newVm.initialization = params.Initialization()
newVm.initialization.set_regenerate_ids(True)
newVm.initialization.configuration = params.Configuration()
newVm.initialization.configuration.set_type("ovf")
newVm.initialization.configuration.set_data(configuration_data)
my_vm = api.vms.add(newVm)


DOMAIN_NAME = 'sdffds'
MB=1024*1024
INTERFACE='virtio'
FORMAT='qcow'

#Create a disk to restore the data to and attach it to that VM
storage_domain = api.storagedomains.get(DOMAIN_NAME)

#Find the VM that has access to the backup:
vm_backup_access = api.vms.get(VM_THAT_PERFORM_BACKUP)

#Create a new disk and attach it to the VM with access to the backed up data.
target_storage=params.StorageDomains(storage_domain={storage_domain})
created_disk=vm_backup_access.disks.add(params.Disk(storage_domains=target_storage, interface='virtio', format='cow', provisioned_size=1024*MB))

while vm_backup_access.disks.get(id=created_disk.get_id()).get_status() == 'locked':
    sleep(1)

#Restore the data to the disk/disks.

#Detach the disk from the VM with the access to the backup and attach it to the restored VM (see in the backup flow)

# Bye:
api.disconnect()
