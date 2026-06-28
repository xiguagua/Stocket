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
