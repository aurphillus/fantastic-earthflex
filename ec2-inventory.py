import boto3
import botocore
import pandas as pd
import datetime

holding = []

class InstanceInventory:
    
    # init function
    def __init__(self):
        self.aws_service = "ec2"
        self.session = boto3.Session(profile_name="default")
        # self.session = boto3.Session(profile_name='personal')
        self.holding = []

    def get_all_regions(self) -> list:
        """
        Get all regions
        :return: list of regions
        """
        regions = []
        for region in self.session.get_available_regions(self.aws_service):
            regions.append(region)
        return regions

    def get_all_instances(self,region: str) -> list:
        """
        Get all instances in a region
        :param region: region to get instances from
        :return: list of instances
        """
        ec2 = self.session.client(self.aws_service, region_name=region)
        instances = []
        try:
            response = ec2.describe_instances()
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    instances.append(instance)
        except botocore.exceptions.ClientError as e:
            print(e)
        return instances

    def get_all_instances_by_tag(self, region: str, tag: str) -> list:
        """
        Get all instances with a tag in a region
        :param region: region to get instances from
        :param tag: tag to search for
        :return: list of instances
        """
        ec2 = self.session.client(self.aws_service, region_name=region)
        instances = []
        try:
            response = ec2.describe_instances(Filters=[{'Name': 'tag:' + tag}])
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    instances.append(instance)
        except botocore.exceptions.ClientError as e:
            print(e)
        return instances

    def get_all_instances_by_tag_value(self, region: str, tag: str, value: str) -> list:
        """
        Get all instances with a tag in a region
        :param region: region to get instances from
        :param tag: tag to search for
        :param value: value to search for
        :return: list of instances
        """
        ec2 = self.session.client(self.aws_service, region_name=region)
        instances = []
        try:
            response = ec2.describe_instances(Filters=[{'Name': 'tag:' + tag, 'Values': [value]}])
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    instances.append(instance)
        except botocore.exceptions.ClientError as e:
            print(e)
        return instances

    def instance_record(self, instance: dict, region: str):
        """
        Create a record for an instance
        :param instance: instance to create record for
        :param region: region of instance
        """

        record = {}
        record["id"] = instance["InstanceId"]
        # tags
        name = ""
        if "Tags" in instance.keys():
            tags = instance["Tags"]
            for tag in tags:
                if tag["Key"] == "Name":
                    name = tag["Value"]
        record["name"] = name if len(name) > 0 else "-"
        record["instance_type"] = instance["InstanceType"]
        record["state"] = instance["State"]["Name"]
        record["public_ip"] = instance["PublicIpAddress"] if "PublicIpAddress" in instance.keys() else "-"
        record["private_ip"] = instance["PrivateIpAddress"] if "PrivateIpAddress" in instance.keys() else "-"
        record["platform"] = instance["PlatformDetails"]
        
        record["region"] = region
        launch_time = instance["LaunchTime"]
        launch_time = launch_time.replace(tzinfo=None)
        if record["state"] in ["terminated", "stopped"]:
            record["uptime"] = "-"
        else:
            uptime = datetime.datetime.utcnow() - launch_time
            uptime_seconds = uptime.total_seconds()
            diff_time = uptime_seconds // 3600
            if diff_time == 0:
                diff_time = uptime_seconds // 60
                diff_time = int(diff_time)
                diff_time = f"{diff_time} minutes"
            elif diff_time > 24:
                diff_time = diff_time // 24
                diff_time = int(diff_time)
                diff_time = f"{diff_time} days"
            else:
                diff_time = round(diff_time, 0)
                diff_time = int(diff_time)
                diff_time = f"{diff_time} hours"
            record["uptime"] = str(diff_time)
        record["region"] = region
        holding.append(record)
        return record

    def controller(self):
        regions = self.get_all_regions()
        regions = ["ap-south-1"]
        for region in regions:
            print("Region: " + region)
            # instances = self.get_all_instances(region)
            instances = self.get_all_instances_by_tag(region, "Type")
            for instance in instances:
                self.instance_record(instance, region)

        df = pd.DataFrame(holding)
        print(df)
        df.to_csv("instances.csv",index=False)

if __name__ == "__main__":
    ec2 = InstanceInventory()
    ec2.controller()