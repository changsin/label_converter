import attr


@attr.s(slots=True, frozen=False)
class AdqLabels:
    twconverted = attr.ib(default=None, validator=attr.validators.instance_of(str))
    mode = attr.ib(default="annotation", validator=attr.validators.instance_of(str))
    template_version = attr.ib(default="0.1", validator=attr.validators.instance_of(str))
    images = attr.ib(default=[], validator=attr.validators.instance_of(list))
    meta_data = attr.ib(default=None)

    # {
    #     "mode": "annotation",
    #     "twconverted": "96E7D8C8-44E4-4055-8487-85B3208E51A2",
    #     "template_version": "0.1",
    #     "images": [

    def to_json(self):
        return {
            "twconverted": self.twconverted,
            "mode": self.mode,
            "template_version": self.template_version,
            "images": self.images,
            "meta_data": self.meta_data
        }

    @staticmethod
    def from_json(json_dict):
        return AdqLabels(
            twconverted=json_dict['twconverted'],
            mode=json_dict['mode'],
            template_version=json_dict['template_version'],
            images=[AdqLabels.Image.from_json(json_image) for json_image in json_dict['images']],
            meta_data=json_dict['meta_data']
        )

    @attr.s(slots=True, frozen=False)
    class Image:
        image_id = attr.ib(validator=attr.validators.instance_of(str))
        name = attr.ib(validator=attr.validators.instance_of(str))
        width = attr.ib(validator=attr.validators.instance_of(str))
        height = attr.ib(validator=attr.validators.instance_of(str))
        objects = attr.ib(default=[], validator=attr.validators.instance_of(list))

        # {
        #     "image_id": "0",
        #     "name": "WIN_20220913_14_01_16_Pro.jpg",
        #     "width": "3840",
        #     "height": "2160",
        #     "objects": [
        #
        # {

        def to_json(self):
            return {
                "image_id": self.image_id,
                "name": self.name,
                "width": self.width,
                "height": self.height,
                "objects": self.objects
            }

        @staticmethod
        def from_json(json_dict):
            return AdqLabels.Image(
                image_id=json_dict['image_id'],
                name=json_dict['name'],
                width=json_dict['width'],
                height=json_dict['height'],
                objects=[AdqLabels.Object.from_json(json_obj) for json_obj in json_dict['objects']]
            )

    @attr.s(slots=True, frozen=False)
    class Object:
        label = attr.ib(validator=attr.validators.instance_of(str))
        type = attr.ib(validator=attr.validators.instance_of(str))
        occluded = attr.ib(validator=attr.validators.instance_of(str))
        z_order = attr.ib(validator=attr.validators.instance_of(str))
        group_id = attr.ib(validator=attr.validators.instance_of(str))
        position = attr.ib(validator=attr.validators.instance_of(str))
        # a list of attribute_name and attribute_value pairs
        attributes = attr.ib(default=[], validator=attr.validators.instance_of(list))
        verification_result = attr.ib(default=None)

        # {
        #   "label": "4FM",
        #   "type": "box",
        #   "occluded": "0",
        #   "z_order": "7",
        #   "group_id": "",
        #   "position": "387.50000000, 195.90039062, 2034.10156250, 1256.60036621",
        #   "attributes": [],
        #   "verification_result": {
        #     "error_code": "DVE_RANGE",
        #     "comment": ""
        #   }
        # },
        # {
        #   "label": "UNTAG",
        #   "type": "box",
        #   "position": "1730, 1502, 1740, 1512",
        #   "occluded": "0",
        #   "z_order": "1",
        #   "verification_result": {
        #     "error_code": "DVE_UNTAG",
        #     "comment": ""
        #   }
        # }

        def to_json(self):
            return {
                "label": self.label,
                "type": self.type,
                "occluded": self.occluded,
                "z_order": self.z_order,
                "group_id": self.group_id,
                "position": self.position,
                "attributes": self.attributes,
                "verification_result": self.verification_result,
            }

        @staticmethod
        def from_json(json_dict):
            verification_result = None
            if json_dict.get('verification_result'):
                verification_result = ['verification_result']

            return AdqLabels.Object(label=json_dict['label'],
                                    type=json_dict['type'],
                                    occluded=json_dict['occluded'],
                                    z_order=json_dict['z_order'],
                                    group_id=json_dict['group_id'],
                                    position=json_dict['position'],
                                    attributes=json_dict['attributes'],
                                    verification_result=verification_result)
