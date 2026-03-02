from setuptools import setup

package_name = 'auv_bringup'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/auv_system.launch.py']),
        ('share/' + package_name + '/config', ['config/auv_system.params.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='auv-dev',
    maintainer_email='dev@example.com',
    description='AUV bringup and mission manager',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mission_manager = auv_bringup.mission_manager:main',
            'api_bridge = auv_bringup.api_bridge:main',
        ],
    },
)
