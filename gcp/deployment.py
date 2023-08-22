class Resource(object):
    name: str = ""
    type: str = ""
    properties: dict = {}
    metadata: dict = None
    ref_elem: str = "selfLink"

    @property
    def resource(self) -> dict:
        r = {
            'name': self.name,
            'type': self.type,
            'properties': self.properties,
        }
        if self.metadata:
            r['metadata'] = self.metadata
        return r

    @property
    def ref(self) -> str:
        return f'$(ref.{self.name}.{self.ref_elem})'

    def __init__(self, name: str, properties: dict, depends: list['Resource']=None):
        self.name = name
        self.properties = properties
        if depends:
            self.metadata = {
                'dependsOn': [x.name for x in depends],
            }


class Network(Resource):
    type = 'compute.v1.network'


class Subnetwork(Resource):
    type = 'compute.v1.subnetwork'


class ServiceAccount(Resource):
    type = 'iam.v1.serviceAccount'
    ref_elem = 'email'

    def __init__(self, name: str, properties: dict, access_control: list[str]=None):
        super(ServiceAccount, self).__init__(name, properties)
        self.access_control = access_control

    @property
    def resource(self) -> dict:
        r = super(ServiceAccount, self).resource
        if self.access_control:
            r['accessControl'] = {
                'gcpIamPolicy': {
                    'bindings': [
                        {
                            'role': 'roles/iam.serviceAccountTokenCreator',
                            'members': [f'serviceAccount:{x}' for x in self.access_control],
                        }
                    ],
                },
            }
        return r


class Role(Resource):
    type = 'gcp-types/iam-v1:projects.roles'
    ref_elem = 'name'


class IamMemberBinding(Resource):
    type = 'gcp-types/cloudresourcemanager-v1:virtual.projects.iamMemberBinding'


def generate_config(context):
    name = context.properties['name']
    region = context.properties['region']

    network = Network(f'dc-network-{name}', {
        'name': 'network',
        'autoCreateSubnetworks': False,
        'mtu': 8896,
        'routingConfig': {
            'routingMode': 'REGIONAL',
        },
    })

    subnetwork = Subnetwork(f'dc-network-{name}-{region}', {
        'name': 'subnetwork',
        'description:': f'DoubleCloud BYOC {name} in {region}',
        'ipCidrRange': context.properties['cidr'],
        'ipv6AccessType': 'EXTERNAL',
        'region': region,
        'network': network.ref,
        'stackType': 'IPV4_IPV6',
    }, [network])

    service_account = ServiceAccount('sa', {
        'accountId': f'dc-byoc-{name}',
        'displayName': f'DoubleCloud BYOC',
    }, ['controlplane@byoa-doublecloud.iam.gserviceaccount.com'])

    role = Role('role', {
        'parent': 'projects/' + context.env['project'],
        'roleId': f'dc_byoc_{name.replace("-", "_")}',
        'role': {
            'includedPermissions': [
                "cloudkms.cryptoKeyVersions.destroy",
                "cloudkms.cryptoKeyVersions.list",
                "cloudkms.cryptoKeys.create",
                "cloudkms.cryptoKeys.get",
                "cloudkms.cryptoKeys.getIamPolicy",
                "cloudkms.cryptoKeys.setIamPolicy",
                "cloudkms.cryptoKeys.update",
                "cloudkms.keyRings.create",
                "cloudkms.keyRings.get",

                "compute.addresses.createInternal",
                "compute.addresses.deleteInternal",
                "compute.addresses.get",
                "compute.addresses.use",
                "compute.disks.create",
                "compute.disks.resize",
                "compute.firewalls.create",
                "compute.forwardingRules.create",
                "compute.forwardingRules.delete",
                "compute.forwardingRules.pscCreate",
                "compute.forwardingRules.pscDelete",
                "compute.globalOperations.get",
                "compute.images.getFromFamily",
                "compute.images.useReadOnly",
                "compute.instances.create",
                "compute.instances.delete",
                "compute.instances.get",
                "compute.instances.setMetadata",
                "compute.instances.setServiceAccount",
                "compute.instances.start",
                "compute.instances.stop",
                "compute.instances.update",
                "compute.networks.addPeering",
                "compute.networks.create",
                "compute.networks.get",
                "compute.networks.removePeering",
                "compute.networks.updatePolicy",
                "compute.networks.use",
                "compute.regionOperations.get",
                "compute.subnetworks.create",
                "compute.subnetworks.delete",
                "compute.subnetworks.get",
                "compute.subnetworks.use",
                "compute.subnetworks.useExternalIp",
                "compute.zoneOperations.get",

                "dns.changes.create",
                "dns.managedZones.create",
                "dns.networks.bindPrivateDNSZone",
                "dns.resourceRecordSets.create",
                "dns.resourceRecordSets.delete",
                "dns.resourceRecordSets.get",
                "dns.resourceRecordSets.update",

                "iam.serviceAccounts.actAs",
                "iam.serviceAccounts.create",
                "iam.serviceAccounts.delete",
                "iam.serviceAccounts.get",
                "iam.serviceAccounts.getIamPolicy",
                "iam.serviceAccounts.list",

                "resourcemanager.projects.get",
                "resourcemanager.projects.getIamPolicy",
                "resourcemanager.projects.setIamPolicy",

                "servicedirectory.services.create",
                "servicedirectory.services.delete",
                "servicedirectory.namespaces.create",

                "storage.buckets.create",
                "storage.buckets.delete",
                "storage.buckets.get",
                "storage.buckets.getIamPolicy",
                "storage.buckets.setIamPolicy",
                "storage.buckets.update",
                "storage.hmacKeys.create",
                "storage.hmacKeys.delete",
                "storage.hmacKeys.list",
                "storage.hmacKeys.update",
                "storage.objects.get",
                "storage.objects.delete",
                "storage.objects.list",
            ],
        },
    })

    role_bindings = IamMemberBinding('bindings', {
        'resource': context.env['project'],
        'role': role.ref,
        'member': f'serviceAccount:{service_account.ref}'
    }, [role, service_account])

    return {
        'resources': [
            network.resource,
            subnetwork.resource,
            service_account.resource,
            role.resource,
            role_bindings.resource,
        ],
        'outputs': [
            {
                'name': 'service_account_email',
                'value': service_account.ref,
            },
            {
                'name': 'project_name',
                'value': context.env['project'],
            },
            {
                'name': 'network_name',
                'value': f'dc-network-{name}',
            },
            {
                'name': 'region_id',
                'value': region,
            },
            {
                'name': 'subnetwork_name',
                'value': f'dc-network-{name}-{region}',
            },
        ],
    }
