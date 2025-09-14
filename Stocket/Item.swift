//
//  Item.swift
//  Stocket
//
//  Created by 黄城 on 2025/9/14.
//

import Foundation
import SwiftData

@Model
final class Item {
    var timestamp: Date
    
    init(timestamp: Date) {
        self.timestamp = timestamp
    }
}
