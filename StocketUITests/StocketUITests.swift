//
//  StocketUITests.swift
//  StocketUITests
//
//  Created by 黄城 on 2025/9/14.
//

import XCTest

final class StocketUITests: XCTestCase {

    override func setUpWithError() throws {
        // Put setup code here. This method is called before the invocation of each test method in the class.

        // In UI tests it is usually best to stop immediately when a failure occurs.
        continueAfterFailure = false

        // In UI tests it’s important to set the initial state - such as interface orientation - required for your tests before they run. The setUp method is a good place to do this.
    }

    override func tearDownWithError() throws {
        // Put teardown code here. This method is called after the invocation of each test method in the class.
    }

    @MainActor
    func testAddTickerAndShowTodayEvent() throws {
        let app = XCUIApplication()
        app.launchEnvironment["WORKER_HOST"] = "127.0.0.1"
        app.launchEnvironment["WORKER_PORT"] = "8787"
        app.launch()

        app.tabBars.buttons["Portfolio"].tap()
        app.buttons["portfolio.addTicker"].tap()

        let searchField = app.searchFields["Search ticker or company name"]
        XCTAssertTrue(searchField.waitForExistence(timeout: 5))
        searchField.tap()
        searchField.typeText("AAPL")

        let aaplResult = app.buttons["AAPL"]
        XCTAssertTrue(aaplResult.waitForExistence(timeout: 5))
        aaplResult.tap()

        XCTAssertTrue(app.staticTexts["AAPL"].waitForExistence(timeout: 5))

        app.tabBars.buttons["Today"].tap()
        XCTAssertTrue(app.staticTexts["Company filed a current report."].waitForExistence(timeout: 10))
    }

    @MainActor
    func testLaunchPerformance() throws {
        // This measures how long it takes to launch your application.
        measure(metrics: [XCTApplicationLaunchMetric()]) {
            XCUIApplication().launch()
        }
    }
}
