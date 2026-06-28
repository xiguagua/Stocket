import CoreGraphics

enum Theme {
    enum Spacing: CGFloat {
        case pt2 = 2
        case pt4 = 4
        case pt8 = 8
        case pt12 = 12
        case pt16 = 16
        case pt20 = 20
        case pt24 = 24
        case pt32 = 32
        case pt48 = 48

        var value: CGFloat { rawValue }
    }
}

// MARK: - Global Spacing Constants

let pt2 = Theme.Spacing.pt2.rawValue
let pt4 = Theme.Spacing.pt4.rawValue
let pt8 = Theme.Spacing.pt8.rawValue
let pt12 = Theme.Spacing.pt12.rawValue
let pt16 = Theme.Spacing.pt16.rawValue
let pt20 = Theme.Spacing.pt20.rawValue
let pt24 = Theme.Spacing.pt24.rawValue
let pt32 = Theme.Spacing.pt32.rawValue
let pt48 = Theme.Spacing.pt48.rawValue
