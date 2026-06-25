// swift-tools-version: 6.2

import PackageDescription

let package = Package(
    name: "STLibrary",
    platforms: [
//        .macOS(.v15),
        .iOS(.v18)
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
