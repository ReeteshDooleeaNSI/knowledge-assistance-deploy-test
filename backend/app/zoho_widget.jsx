<Card size="sm">
    <Col gap={2}>
      <Row>
        <Title value={`Ticket #${ticketNumber}`} size="sm" />
        <Spacer />
        {overdue ? (
          <Badge label={`Overdue ${overdueBy}`} color="danger" />
        ) : (
          <Badge label="On time" color="success" />
        )}
      </Row>
  
      <Text value={subject} maxLines={2} />
  
      <Row gap={2}>
        <Badge label={status} color="info" />
        <Badge label={statusType} />
        <Badge label={channel} />
        <Badge label={product} />
      </Row>
    </Col>
  
    <Divider flush />
  
    <Col gap={1}>
      <Row>
        <Caption value={`Last update • ${lastUpdateTime}`} />
      </Row>
      <Text value={lastUpdateSnippet} size="sm" maxLines={2} />
    </Col>
  
    <Divider />
  
    <Col gap={2}>
      <Row>
        <Caption value="Contact" />
        <Spacer />
        <Text value={`${contactName} • ${accountName}`} size="sm" maxLines={1} />
      </Row>
      <Row>
        <Caption value="Due" />
        <Spacer />
        <Text
          value={dueDate}
          size="sm"
          color={overdue ? "danger" : "secondary"}
        />
      </Row>
      <Row>
        <Caption value="Department" />
        <Spacer />
        <Text value={departmentName} size="sm" maxLines={1} />
      </Row>
      <Row>
        <Caption value="Modified" />
        <Spacer />
        <Text value={modifiedTime} size="sm" />
      </Row>
    </Col>
  
    <Divider />
  
    <Row>
      <Button
        label="Open in Zoho Desk"
        style="primary"
        onClickAction={{
          type: "ticket.open",
          payload: { id: ticketId, url: webUrl },
        }}
      />
      <Button
        label="Add note"
        variant="outline"
        onClickAction={{ type: "ticket.add_note", payload: { id: ticketId } }}
      />
    </Row>
  </Card>