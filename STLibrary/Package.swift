// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "STLibrary",
    platforms: [
        .macOS(.v15)
    ],
    products: [
        .library(
            name: "STLibrary",
            targets: ["STLibrary"]
        )
    ],
    targets: [
        .target(name: "STLibrary"),
        .testTarget(
            name: "STLibraryTests",
            dependencies: ["STLibrary"]
        )
    ]
)
