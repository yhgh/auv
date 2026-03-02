from setuptools import setup

package_name = 'auv_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    extras_require={'mavlink': ['pymavlink>=2.4.41']},
    zip_safe=True,
    maintainer='auv-dev',
    maintainer_email='dev@example.com',
    description='AUV control nodes',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'telemetry_bridge = auv_control.telemetry_bridge:main',
            'depth_hold_controller = auv_control.depth_hold_controller:main',
        ],
    },
)
